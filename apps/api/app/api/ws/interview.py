from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session
from app.modules.interview.deps import get_interviewer_agent
from app.modules.interview.orchestrator import InterviewOrchestrator
from app.modules.interview.repository import InterviewRepository
from app.modules.voice.pipeline.voice_pipeline import VoicePipeline
from app.modules.voice.providers.factory import get_voice_providers
from app.modules.voice.ws.connection import VoiceConnectionHandler
from app.modules.voice.ws.manager import VoiceConnectionManager

router = APIRouter(tags=["voice"])
connection_manager = VoiceConnectionManager()


def _parse_user_id(user_id: str = Query(..., alias="user_id")) -> UUID:
    return UUID(user_id)


def build_voice_connection_handler(
    websocket: WebSocket,
    session_id: UUID,
    user_id: UUID,
    db_session: AsyncSession,
) -> VoiceConnectionHandler:
    repository = InterviewRepository(db_session)
    orchestrator = InterviewOrchestrator(repository, get_interviewer_agent())
    providers = get_voice_providers()

    async def emit(message: dict) -> None:
        await websocket.send_json(message)

    pipeline = VoicePipeline(
        orchestrator,
        providers.stt,
        providers.tts,
        emit=emit,
    )

    return VoiceConnectionHandler(
        websocket,
        session_id,
        user_id,
        orchestrator,
        pipeline,
    )


@router.websocket("/ws/interview/{session_id}")
async def interview_voice_ws(
    websocket: WebSocket,
    session_id: UUID,
    user_id: UUID = Depends(_parse_user_id),
    db_session: AsyncSession = Depends(get_async_session),
) -> None:
    handler = build_voice_connection_handler(websocket, session_id, user_id, db_session)

    await connection_manager.register(session_id, websocket)
    try:
        await handler.run()
    finally:
        connection_manager.unregister(session_id)
