from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket

from app.config import settings
from app.core.rate_limit import SlidingWindowLimiter
from app.modules.auth.ws import parse_ws_user_id
from app.modules.interview.deps import get_interviewer_agent
from app.modules.interview.scoped_orchestrator import SessionScopedOrchestrator
from app.modules.voice.pipeline.voice_pipeline import VoicePipeline
from app.modules.voice.providers.factory import get_voice_providers
from app.modules.voice.ws.connection import VoiceConnectionHandler
from app.modules.voice.ws.manager import VoiceConnectionManager

router = APIRouter(tags=["voice"])
connection_manager = VoiceConnectionManager()

# Close codes for connection-policy rejections.
RATE_LIMITED_CLOSE_CODE = 4008
TOO_MANY_CONNECTIONS_CLOSE_CODE = 4009

_connect_limiter = SlidingWindowLimiter(
    limit=settings.ws_connect_rate_limit_per_minute, window_seconds=60.0
)


def build_voice_connection_handler(
    websocket: WebSocket,
    session_id: UUID,
    user_id: UUID,
) -> VoiceConnectionHandler:
    # The orchestrator opens a fresh DB session per operation: WebSocket
    # connections are long-lived and background turn tasks run concurrently
    # with the receive loop, so no single AsyncSession may be shared.
    orchestrator = SessionScopedOrchestrator(get_interviewer_agent())
    providers = get_voice_providers()

    pipeline = VoicePipeline(
        orchestrator,
        providers.stt,
        providers.tts,
    )

    return VoiceConnectionHandler(
        websocket,
        session_id,
        user_id,
        orchestrator,
        pipeline,
        manager=connection_manager,
    )


@router.websocket("/ws/interview/{session_id}")
async def interview_voice_ws(
    websocket: WebSocket,
    session_id: UUID,
    user_id: UUID = Depends(parse_ws_user_id),
) -> None:
    if settings.rate_limit_enabled and not settings.is_test:
        if not _connect_limiter.check(f"ws-connect:{user_id}"):
            await websocket.close(code=RATE_LIMITED_CLOSE_CODE, reason="Rate limited")
            return
        already_connected = connection_manager.is_connected(session_id)
        if (
            not already_connected
            and connection_manager.user_connection_count(user_id)
            >= settings.ws_max_connections_per_user
        ):
            await websocket.close(
                code=TOO_MANY_CONNECTIONS_CLOSE_CODE, reason="Too many connections"
            )
            return

    handler = build_voice_connection_handler(websocket, session_id, user_id)

    await connection_manager.register(session_id, websocket, user_id=user_id)
    try:
        await handler.run()
    finally:
        connection_manager.unregister(session_id, websocket)
