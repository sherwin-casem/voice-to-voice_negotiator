from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session
from app.modules.interview.interviewer_agent import InterviewerAgent, MockInterviewerLLMProvider
from app.modules.interview.orchestrator import InterviewOrchestrator
from app.modules.interview.repository import InterviewRepository
from app.modules.voice.pipeline.voice_pipeline import VoicePipeline
from app.modules.voice.providers.mock import MockSpeechToTextProvider, MockTextToSpeechProvider
from app.modules.voice.ws.connection import VoiceConnectionHandler
from app.modules.voice.ws.manager import VoiceConnectionManager

router = APIRouter(tags=["voice"])
connection_manager = VoiceConnectionManager()


def _parse_user_id(user_id: str = Query(..., alias="user_id")) -> UUID:
    return UUID(user_id)


@router.websocket("/ws/interview/{session_id}")
async def interview_voice_ws(
    websocket: WebSocket,
    session_id: UUID,
    user_id: UUID = Depends(_parse_user_id),
    db_session: AsyncSession = Depends(get_async_session),
) -> None:
    repository = InterviewRepository(db_session)
    orchestrator = InterviewOrchestrator(
        repository,
        InterviewerAgent(MockInterviewerLLMProvider()),
    )

    async def emit(message: dict) -> None:
        await websocket.send_json(message)

    pipeline = VoicePipeline(
        orchestrator,
        MockSpeechToTextProvider(),
        MockTextToSpeechProvider(),
        emit=emit,
    )

    handler = VoiceConnectionHandler(
        websocket,
        session_id,
        user_id,
        orchestrator,
        pipeline,
    )

    await connection_manager.register(session_id, websocket)
    try:
        await handler.run()
    finally:
        connection_manager.unregister(session_id)
