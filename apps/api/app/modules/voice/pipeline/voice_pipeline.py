import base64
import logging
import time
from collections.abc import Awaitable, Callable
from uuid import UUID

from app.config import settings
from app.core.exceptions import AppError, MaxQuestionsReachedError
from app.db.enums import InterviewSessionStatus
from app.modules.evaluation.runner import schedule_session_evaluation
from app.modules.interview.orchestrator import InterviewOrchestrator
from app.modules.interview.scoped_orchestrator import SessionScopedOrchestrator
from app.modules.voice.pipeline.turn_buffer import TurnAudioBuffer
from app.modules.voice.providers.base import SpeechToTextProvider, TextToSpeechProvider
from app.modules.voice.protocol.events import (
    AudioOutputPayload,
    InterviewerResponsePayload,
    InterviewerThinkingPayload,
    SessionEndedPayload,
    SessionErrorPayload,
    TranscriptFinalPayload,
    TranscriptPartialPayload,
)
from app.modules.voice.protocol.parser import build_server_envelope
from app.modules.voice.protocol.types import (
    AUDIO_OUTPUT,
    INTERVIEWER_RESPONSE,
    INTERVIEWER_THINKING,
    SESSION_ENDED,
    SESSION_ERROR,
    TRANSCRIPT_FINAL,
    TRANSCRIPT_PARTIAL,
)

logger = logging.getLogger(__name__)

EmitFn = Callable[[dict], Awaitable[None]]


class VoicePipeline:
    """Audio transport pipeline: STT → interview orchestrator → TTS.

    Keeps audio provider details separate from interview business logic.
    """

    def __init__(
        self,
        orchestrator: "InterviewOrchestrator | SessionScopedOrchestrator",
        stt_provider: SpeechToTextProvider,
        tts_provider: TextToSpeechProvider,
        *,
        emit: EmitFn | None = None,
    ) -> None:
        self._orchestrator = orchestrator
        self._stt = stt_provider
        self._tts = tts_provider
        self._emit_fn = emit
        self._turn_buffer = TurnAudioBuffer(
            max_chunk_bytes=settings.ws_max_audio_chunk_bytes,
            max_turn_bytes=settings.ws_max_turn_audio_bytes,
        )
        self._current_question_id: UUID | None = None
        self._processing = False
        self._cancel_tts = False
        self._end_after_answer = False
        self._on_session_complete: Callable[[], Awaitable[None]] | None = None

    def set_session_complete_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        """Invoked after a server-initiated session end so the transport can close."""
        self._on_session_complete = callback

    def set_emit(self, emit: EmitFn) -> None:
        """Route output through the connection handler's guarded send."""
        self._emit_fn = emit

    async def _emit(self, message: dict) -> None:
        if self._emit_fn is None:
            raise RuntimeError("VoicePipeline emit function is not configured")
        await self._emit_fn(message)

    @property
    def current_question_id(self) -> UUID | None:
        return self._current_question_id

    def set_current_question(self, question_id: UUID) -> None:
        self._current_question_id = question_id

    def configure_audio_format(self, sample_rate: int, encoding: str, channels: int) -> None:
        self._turn_buffer.sample_rate = sample_rate
        self._turn_buffer.encoding = encoding
        self._turn_buffer.channels = channels

    async def deliver_interviewer_turn(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        question_id: UUID,
        text: str,
        topic_tag: str | None,
        should_end_session: bool,
        request_id: str | None = None,
    ) -> None:
        self._current_question_id = question_id
        self._end_after_answer = should_end_session
        await self._emit(
            build_server_envelope(
                INTERVIEWER_RESPONSE,
                InterviewerResponsePayload(
                    question_id=question_id,
                    text=text,
                    topic_tag=topic_tag,
                    should_end_session=should_end_session,
                ),
                request_id=request_id,
                timestamp_ms=_now_ms(),
            )
        )
        await self._stream_tts(text, request_id=request_id)

    async def append_audio_input(self, seq: int, data_b64: str) -> None:
        self._turn_buffer.append(seq, data_b64)

    async def process_speech_end(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        request_id: str | None = None,
    ) -> None:
        if self._processing:
            await self._emit_error(
                "PIPELINE_BUSY",
                "Previous turn is still processing",
                recoverable=True,
                request_id=request_id,
            )
            return

        if self._current_question_id is None:
            await self._emit_error(
                "NO_ACTIVE_QUESTION",
                "No interviewer question is active",
                recoverable=True,
                request_id=request_id,
            )
            return

        audio = self._turn_buffer.consume()
        if not audio:
            await self._emit_error(
                "EMPTY_AUDIO",
                "No audio received for this turn",
                recoverable=True,
                request_id=request_id,
            )
            return

        self._processing = True
        try:
            await self._run_turn_pipeline(
                session_id=session_id,
                user_id=user_id,
                question_id=self._current_question_id,
                audio=audio,
                request_id=request_id,
            )
        except AppError as exc:
            await self._emit_error(exc.code, exc.message, recoverable=False, request_id=request_id)
        except Exception:
            # STT/TTS provider failures, schema errors, DB errors: surface a
            # structured error to the client instead of silently killing the task.
            logger.exception(
                "Voice turn processing failed",
                extra={"component": "voice_pipeline", "session_id": str(session_id)},
            )
            await self._emit_error(
                "TURN_PROCESSING_FAILED",
                "Processing your answer failed. Please try again.",
                recoverable=True,
                request_id=request_id,
            )
        finally:
            self._processing = False

    async def emit_error(
        self,
        code: str,
        message: str,
        *,
        recoverable: bool,
        request_id: str | None,
    ) -> None:
        await self._emit_error(code, message, recoverable=recoverable, request_id=request_id)

    async def cancel_output(self) -> None:
        self._cancel_tts = True

    async def _run_turn_pipeline(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        question_id: UUID,
        audio: bytes,
        request_id: str | None,
    ) -> None:
        stt_start = time.perf_counter()
        async for transcript in self._stt.stream_transcribe(
            audio,
            sample_rate=self._turn_buffer.sample_rate,
        ):
            if not transcript.is_final:
                await self._emit(
                    build_server_envelope(
                        TRANSCRIPT_PARTIAL,
                        TranscriptPartialPayload(text=transcript.text),
                        request_id=request_id,
                        timestamp_ms=_now_ms(),
                    )
                )
                continue

            self._log_stage_latency("stt", stt_start, session_id)

            await self._emit(
                build_server_envelope(
                    TRANSCRIPT_FINAL,
                    TranscriptFinalPayload(text=transcript.text, question_id=question_id),
                    request_id=request_id,
                    timestamp_ms=_now_ms(),
                )
            )

            await self._orchestrator.submit_answer(
                session_id,
                user_id,
                question_id,
                answer_text=transcript.text,
            )

            if self._end_after_answer:
                # The answered question was the interviewer's closing question.
                await self._complete_session(
                    session_id,
                    user_id,
                    reason="interviewer_ended",
                    request_id=request_id,
                )
                return

            await self._emit(
                build_server_envelope(
                    INTERVIEWER_THINKING,
                    InterviewerThinkingPayload(question_id=question_id),
                    request_id=request_id,
                    timestamp_ms=_now_ms(),
                )
            )

            llm_start = time.perf_counter()
            try:
                result = await self._orchestrator.ask_next_question(session_id, user_id)
                self._log_stage_latency("llm", llm_start, session_id)
            except MaxQuestionsReachedError:
                # Backstop for interviewer agents that never flag a closing
                # question: end gracefully instead of surfacing a conflict.
                await self._complete_session(
                    session_id,
                    user_id,
                    reason="max_questions_reached",
                    request_id=request_id,
                )
                return
            except AppError as exc:
                await self._emit_error(exc.code, exc.message, recoverable=False, request_id=request_id)
                return

            await self.deliver_interviewer_turn(
                session_id=session_id,
                user_id=user_id,
                question_id=result.question.id,
                text=result.question.question_text,
                topic_tag=result.question.topic_tag,
                should_end_session=result.should_end_session,
                request_id=request_id,
            )

    async def _complete_session(
        self,
        session_id: UUID,
        user_id: UUID,
        *,
        reason: str,
        request_id: str | None,
    ) -> None:
        session = await self._orchestrator.end_session(session_id, user_id, reason=reason)
        if session.status == InterviewSessionStatus.COMPLETING:
            schedule_session_evaluation(session_id, user_id)
        await self._emit(
            build_server_envelope(
                SESSION_ENDED,
                SessionEndedPayload(reason=reason, status=session.status.value),
                request_id=request_id,
                timestamp_ms=_now_ms(),
            )
        )
        if self._on_session_complete is not None:
            await self._on_session_complete()

    def _log_stage_latency(self, stage: str, start: float, session_id: UUID | None = None) -> None:
        extra: dict = {
            "component": "voice_pipeline",
            "stage": stage,
            "latency_ms": int((time.perf_counter() - start) * 1000),
        }
        if session_id is not None:
            extra["session_id"] = str(session_id)
        logger.info("Voice turn stage completed", extra=extra)

    async def _stream_tts(self, text: str, *, request_id: str | None) -> None:
        self._cancel_tts = False
        tts_start = time.perf_counter()
        async for chunk in self._tts.synthesize(text, sample_rate=self._turn_buffer.sample_rate):
            if self._cancel_tts:
                logger.info("TTS output cancelled", extra={"component": "voice_pipeline"})
                break
            if not chunk.data and not chunk.is_final:
                continue
            await self._emit(
                build_server_envelope(
                    AUDIO_OUTPUT,
                    AudioOutputPayload(
                        seq=chunk.seq,
                        data=base64.b64encode(chunk.data).decode("ascii"),
                        encoding=self._turn_buffer.encoding,
                        # Providers dictate their true output rate; fall back to
                        # the negotiated session rate for providers that honor it.
                        sample_rate=chunk.sample_rate or self._turn_buffer.sample_rate,
                        is_final=chunk.is_final,
                    ),
                    request_id=request_id,
                    timestamp_ms=_now_ms(),
                )
            )
        self._log_stage_latency("tts", tts_start)

    async def _emit_error(
        self,
        code: str,
        message: str,
        *,
        recoverable: bool,
        request_id: str | None,
    ) -> None:
        await self._emit(
            build_server_envelope(
                SESSION_ERROR,
                SessionErrorPayload(code=code, message=message, recoverable=recoverable),
                request_id=request_id,
                timestamp_ms=_now_ms(),
            )
        )


def _now_ms() -> int:
    return int(time.time() * 1000)
