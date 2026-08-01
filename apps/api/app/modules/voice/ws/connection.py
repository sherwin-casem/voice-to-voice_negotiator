import asyncio
import logging
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.exceptions import AppError, InvalidStateError
from app.db.enums import InterviewSessionStatus
from app.modules.interview.orchestrator import InterviewOrchestrator
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
    SESSION_END,
    SESSION_ENDED,
    SESSION_READY,
    SESSION_START,
    SPEECH_END,
)

logger = logging.getLogger(__name__)


class VoiceConnectionHandler:
    """Manages WebSocket lifecycle and routes events to the voice pipeline."""

    def __init__(
        self,
        websocket: WebSocket,
        session_id: UUID,
        user_id: UUID,
        orchestrator: InterviewOrchestrator,
        pipeline: VoicePipeline,
    ) -> None:
        self._websocket = websocket
        self._session_id = session_id
        self._user_id = user_id
        self._orchestrator = orchestrator
        self._pipeline = pipeline
        self._started = False
        self._closed = False
        self._tasks: set[asyncio.Task[None]] = set()

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
                    await self._pipeline.emit_error(
                        "SESSION_ALREADY_ACTIVE",
                        "Reconnect to an in-progress session is not supported yet",
                        recoverable=False,
                        request_id=request_id,
                    )
                    return
            else:
                raise InvalidStateError(
                    f"Session must be configured or active to start voice, got {session.status.value}",
                )

            self._started = True
            await self._pipeline.deliver_interviewer_turn(
                session_id=self._session_id,
                user_id=self._user_id,
                question_id=result.question.id,
                text=result.question.question_text,
                topic_tag=result.question.topic_tag,
                should_end_session=result.should_end_session,
                request_id=request_id,
            )
        except AppError as exc:
            await self._pipeline.emit_error(exc.code, exc.message, recoverable=False, request_id=request_id)

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

        task = asyncio.create_task(
            self._pipeline.process_speech_end(
                session_id=self._session_id,
                user_id=self._user_id,
                request_id=request_id,
            )
        )
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _handle_session_end(self, payload, request_id: str | None) -> None:
        session = await self._orchestrator.end_session(
            self._session_id,
            self._user_id,
            reason=payload.reason,
        )
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
        if self._closed:
            return
        self._closed = True

        for task in list(self._tasks):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        if self._started:
            try:
                session = await self._orchestrator.get_session(self._session_id, self._user_id)
                if session.status == InterviewSessionStatus.ACTIVE:
                    await self._orchestrator.abandon_session(
                        self._session_id,
                        self._user_id,
                        reason="disconnect",
                    )
            except AppError:
                logger.warning(
                    "Could not mark session abandoned on disconnect",
                    extra={"component": "voice_ws", "session_id": str(self._session_id)},
                )

        if self._websocket.client_state == WebSocketState.CONNECTED:
            await self._websocket.close()

    async def _close(self) -> None:
        self._closed = True
        if self._websocket.client_state == WebSocketState.CONNECTED:
            await self._websocket.close()
