import asyncio
import logging
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.config import settings
from app.core.exceptions import AppError, InvalidStateError
from app.db.enums import InterviewSessionStatus
from app.modules.evaluation.runner import schedule_session_evaluation
from app.modules.interview.orchestrator import InterviewOrchestrator
from app.modules.interview.scoped_orchestrator import SessionScopedOrchestrator
from app.modules.voice.pipeline.voice_pipeline import VoicePipeline
from app.modules.voice.protocol.events import (
    SessionEndedPayload,
    SessionReadyPayload,
    SessionStartPayload,
)
from app.modules.voice.protocol.parser import (
    ProtocolValidationError,
    build_server_envelope,
    parse_client_envelope,
)
from app.modules.voice.protocol.types import (
    AUDIO_INPUT,
    OUTPUT_CANCEL,
    SESSION_END,
    SESSION_ENDED,
    SESSION_READY,
    SESSION_START,
    SPEECH_END,
)
from app.modules.voice.ws.manager import VoiceConnectionManager

logger = logging.getLogger(__name__)

# Keeps grace-window abandon tasks alive after their handler is gone.
_grace_tasks: set[asyncio.Task] = set()


async def _abandon_after_grace(
    orchestrator: "InterviewOrchestrator | SessionScopedOrchestrator",
    manager: VoiceConnectionManager | None,
    session_id: UUID,
    user_id: UUID,
) -> None:
    """Mark an ACTIVE session abandoned only if the client has not reconnected."""
    await asyncio.sleep(settings.ws_reconnect_grace_seconds)
    if manager is not None and manager.is_connected(session_id):
        return
    try:
        session = await orchestrator.get_session(session_id, user_id)
        if session.status == InterviewSessionStatus.ACTIVE:
            await orchestrator.abandon_session(session_id, user_id, reason="disconnect")
            logger.info(
                "Session abandoned after reconnect grace window",
                extra={"component": "voice_ws", "session_id": str(session_id)},
            )
    except AppError:
        logger.warning(
            "Could not mark session abandoned after grace window",
            extra={"component": "voice_ws", "session_id": str(session_id)},
        )


class VoiceConnectionHandler:
    """Manages WebSocket lifecycle and routes events to the voice pipeline."""

    def __init__(
        self,
        websocket: WebSocket,
        session_id: UUID,
        user_id: UUID,
        orchestrator: "InterviewOrchestrator | SessionScopedOrchestrator",
        pipeline: VoicePipeline,
        manager: VoiceConnectionManager | None = None,
    ) -> None:
        self._websocket = websocket
        self._session_id = session_id
        self._user_id = user_id
        self._orchestrator = orchestrator
        self._pipeline = pipeline
        self._manager = manager
        self._started = False
        self._closed = False
        self._shutdown_started = False
        self._tasks: set[asyncio.Task[None]] = set()
        pipeline.set_session_complete_callback(self._close)
        # All pipeline output flows through the guarded send so in-flight
        # STT/TTS tasks cannot crash on a closed socket.
        pipeline.set_emit(self._send)

    async def run(self) -> None:
        await self._websocket.accept()
        try:
            session = await self._orchestrator.get_session(self._session_id, self._user_id)
            await self._send(
                build_server_envelope(
                    SESSION_READY,
                    SessionReadyPayload(
                        session_id=self._session_id,
                        status=session.status.value,
                        question_count=session.question_count,
                    ),
                )
            )

            while True:
                message = await self._websocket.receive_text()
                await self._handle_message(message)
        except WebSocketDisconnect:
            logger.info(
                "WebSocket disconnected",
                extra={"component": "voice_ws", "session_id": str(self._session_id)},
            )
        except AppError as exc:
            await self._pipeline.emit_error(exc.code, exc.message, recoverable=False, request_id=None)
        finally:
            await self._shutdown()

    async def _handle_message(self, raw: str) -> None:
        try:
            envelope, payload = parse_client_envelope(raw)
        except ProtocolValidationError as exc:
            await self._pipeline.emit_error(exc.code, exc.message, recoverable=True, request_id=None)
            return

        request_id = envelope.request_id

        if envelope.type == SESSION_START:
            await self._handle_session_start(payload, request_id)  # type: ignore[arg-type]
        elif envelope.type == AUDIO_INPUT:
            await self._handle_audio_input(payload, request_id)  # type: ignore[arg-type]
        elif envelope.type == SPEECH_END:
            await self._handle_speech_end(request_id)
        elif envelope.type == OUTPUT_CANCEL:
            await self._pipeline.cancel_output()
        elif envelope.type == SESSION_END:
            await self._handle_session_end(payload, request_id)  # type: ignore[arg-type]
        else:
            await self._pipeline.emit_error(
                "UNKNOWN_EVENT",
                f"Unhandled event type: {envelope.type}",
                recoverable=True,
                request_id=request_id,
            )

    async def _handle_session_start(
        self,
        payload: SessionStartPayload,
        request_id: str | None,
    ) -> None:
        if payload.session_id != self._session_id:
            await self._pipeline.emit_error(
                "SESSION_MISMATCH",
                "session_id in payload does not match WebSocket path",
                recoverable=False,
                request_id=request_id,
            )
            return

        if self._started:
            await self._pipeline.emit_error(
                "ALREADY_STARTED",
                "Voice session already started on this connection",
                recoverable=True,
                request_id=request_id,
            )
            return

        self._pipeline.configure_audio_format(
            payload.audio_format.sample_rate,
            payload.audio_format.encoding,
            payload.audio_format.channels,
        )

        session = await self._orchestrator.get_session(self._session_id, self._user_id)

        try:
            if session.status == InterviewSessionStatus.CONFIGURED:
                result = await self._orchestrator.start(self._session_id, self._user_id)
            elif session.status == InterviewSessionStatus.ACTIVE:
                if session.question_count == 0:
                    result = await self._orchestrator.ask_next_question(self._session_id, self._user_id)
                else:
                    # Reconnect to an in-progress session: re-deliver the open
                    # question, or move to the next one if it was answered.
                    await self._resume_active_session(request_id)
                    return
            else:
                raise InvalidStateError(
                    f"Session must be configured or active to start voice, got {session.status.value}",
                )

            self._started = True
            # TTS synthesis must not block the receive loop.
            self._spawn_task(
                self._deliver_turn_safe(
                    question_id=result.question.id,
                    text=result.question.question_text,
                    topic_tag=result.question.topic_tag,
                    should_end_session=result.should_end_session,
                    request_id=request_id,
                )
            )
        except AppError as exc:
            await self._pipeline.emit_error(exc.code, exc.message, recoverable=False, request_id=request_id)

    async def _resume_active_session(self, request_id: str | None) -> None:
        current = await self._orchestrator.get_current_question(self._session_id, self._user_id)
        if current is None:
            await self._pipeline.emit_error(
                "RESUME_FAILED",
                "Active session has no questions to resume",
                recoverable=False,
                request_id=request_id,
            )
            return

        question, answered = current
        if answered:
            result = await self._orchestrator.ask_next_question(self._session_id, self._user_id)
            question = result.question
            should_end_session = result.should_end_session
        else:
            should_end_session = False

        self._started = True
        self._spawn_task(
            self._deliver_turn_safe(
                question_id=question.id,
                text=question.question_text,
                topic_tag=question.topic_tag,
                should_end_session=should_end_session,
                request_id=request_id,
            )
        )

    async def _deliver_turn_safe(
        self,
        *,
        question_id: UUID,
        text: str,
        topic_tag: str | None,
        should_end_session: bool,
        request_id: str | None,
    ) -> None:
        try:
            await self._pipeline.deliver_interviewer_turn(
                session_id=self._session_id,
                user_id=self._user_id,
                question_id=question_id,
                text=text,
                topic_tag=topic_tag,
                should_end_session=should_end_session,
                request_id=request_id,
            )
        except AppError as exc:
            await self._pipeline.emit_error(exc.code, exc.message, recoverable=False, request_id=request_id)
        except Exception:
            logger.exception(
                "Interviewer turn delivery failed",
                extra={"component": "voice_ws", "session_id": str(self._session_id)},
            )
            await self._pipeline.emit_error(
                "TURN_DELIVERY_FAILED",
                "Delivering the interviewer question failed.",
                recoverable=True,
                request_id=request_id,
            )

    async def _handle_audio_input(self, payload, request_id: str | None) -> None:
        if not self._started:
            await self._pipeline.emit_error(
                "NOT_STARTED",
                "Send session.start before audio.input",
                recoverable=True,
                request_id=request_id,
            )
            return

        try:
            await self._pipeline.append_audio_input(payload.seq, payload.data)
        except ValueError as exc:
            await self._pipeline.emit_error(
                "INVALID_AUDIO_SEQ",
                str(exc),
                recoverable=True,
                request_id=request_id,
            )

    async def _handle_speech_end(self, request_id: str | None) -> None:
        if not self._started:
            await self._pipeline.emit_error(
                "NOT_STARTED",
                "Send session.start before speech.end",
                recoverable=True,
                request_id=request_id,
            )
            return

        self._spawn_task(
            self._pipeline.process_speech_end(
                session_id=self._session_id,
                user_id=self._user_id,
                request_id=request_id,
            )
        )

    def _spawn_task(self, coro) -> None:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._finalize_task)

    def _finalize_task(self, task: asyncio.Task) -> None:
        self._tasks.discard(task)
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.error(
                "Voice turn task failed unexpectedly",
                exc_info=exc,
                extra={"component": "voice_ws", "session_id": str(self._session_id)},
            )

    async def _handle_session_end(self, payload, request_id: str | None) -> None:
        session = await self._orchestrator.end_session(
            self._session_id,
            self._user_id,
            reason=payload.reason,
        )
        if session.status == InterviewSessionStatus.COMPLETING:
            schedule_session_evaluation(self._session_id, self._user_id)
        await self._send(
            build_server_envelope(
                SESSION_ENDED,
                SessionEndedPayload(reason=payload.reason, status=session.status.value),
                request_id=request_id,
            )
        )
        await self._close()

    async def _send(self, message: dict) -> None:
        if self._closed or self._websocket.client_state != WebSocketState.CONNECTED:
            return
        await self._websocket.send_json(message)

    async def _shutdown(self) -> None:
        if self._shutdown_started:
            return
        self._shutdown_started = True
        self._closed = True

        # Stop any in-flight TTS stream and cancel background turn tasks. The
        # current task is skipped so a turn task that triggered the shutdown
        # cannot await its own cancellation.
        await self._pipeline.cancel_output()
        current = asyncio.current_task()
        pending = [task for task in self._tasks if task is not current]
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        if self._started:
            # Give the client a grace window to reconnect before the session
            # is written off as abandoned.
            grace_task = asyncio.create_task(
                _abandon_after_grace(
                    self._orchestrator,
                    self._manager,
                    self._session_id,
                    self._user_id,
                ),
                name=f"voice-grace-{self._session_id}",
            )
            _grace_tasks.add(grace_task)
            grace_task.add_done_callback(_grace_tasks.discard)

        if self._websocket.client_state == WebSocketState.CONNECTED:
            await self._websocket.close()

    async def _close(self) -> None:
        """Server-initiated close after session completion.

        Only stops new sends and closes the socket; full task cleanup happens
        in ``_shutdown`` when the receive loop unwinds.
        """
        self._closed = True
        if self._websocket.client_state == WebSocketState.CONNECTED:
            await self._websocket.close()
