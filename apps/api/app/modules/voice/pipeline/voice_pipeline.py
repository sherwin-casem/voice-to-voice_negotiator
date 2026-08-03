import base64
import logging
import time
from collections.abc import Awaitable, Callable
from uuid import UUID

from app.config import settings
from app.core.exceptions import AppError
from app.modules.interview.orchestrator import InterviewOrchestrator
from app.modules.voice.pipeline.turn_buffer import TurnAudioBuffer
from app.modules.voice.providers.base import SpeechToTextProvider, TextToSpeechProvider
from app.modules.voice.protocol.events import (
    AudioOutputPayload,
    InterviewerResponsePayload,
    InterviewerThinkingPayload,
    SessionErrorPayload,
    TranscriptFinalPayload,
    TranscriptPartialPayload,
)
from app.modules.voice.protocol.parser import build_server_envelope
from app.modules.voice.protocol.types import (
    AUDIO_OUTPUT,
    INTERVIEWER_RESPONSE,
    INTERVIEWER_THINKING,
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
        orchestrator: InterviewOrchestrator,
        stt_provider: SpeechToTextProvider,
        tts_provider: TextToSpeechProvider,
        *,
        emit: EmitFn,
    ) -> None:
        self._orchestrator = orchestrator
        self._stt = stt_provider
        self._tts = tts_provider
        self._emit = emit
        self._turn_buffer = TurnAudioBuffer(
            max_chunk_bytes=settings.ws_max_audio_chunk_bytes,
            max_turn_bytes=settings.ws_max_turn_audio_bytes,
        )
        self._current_question_id: UUID | None = None
        self._processing = False
        self._cancel_tts = False

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

            await self._emit(
                build_server_envelope(
                    INTERVIEWER_THINKING,
                    InterviewerThinkingPayload(question_id=question_id),
                    request_id=request_id,
                    timestamp_ms=_now_ms(),
                )
            )

            try:
                result = await self._orchestrator.ask_next_question(session_id, user_id)
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

    async def _stream_tts(self, text: str, *, request_id: str | None) -> None:
        self._cancel_tts = False
        async for chunk in self._tts.synthesize(text, sample_rate=self._turn_buffer.sample_rate):
            if self._cancel_tts:
                logger.info("TTS output cancelled", extra={"component": "voice_pipeline"})
                break
            await self._emit(
                build_server_envelope(
                    AUDIO_OUTPUT,
                    AudioOutputPayload(
                        seq=chunk.seq,
                        data=base64.b64encode(chunk.data).decode("ascii"),
                        encoding=self._turn_buffer.encoding,
                        sample_rate=self._turn_buffer.sample_rate,
                        is_final=chunk.is_final,
                    ),
                    request_id=request_id,
                    timestamp_ms=_now_ms(),
                )
            )

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
