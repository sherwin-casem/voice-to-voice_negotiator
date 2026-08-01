import pytest

pytestmark = pytest.mark.feature

import json
import uuid
from collections import deque
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from starlette.websockets import WebSocketDisconnect, WebSocketState

from app.db.enums import InterviewSessionStatus, InterviewType
from app.modules.interview.orchestrator import InterviewOrchestrator, QuestionResult
from app.modules.interview.schemas import QuestionRecord, SessionRecord
from app.modules.voice.pipeline.voice_pipeline import VoicePipeline
from app.modules.voice.providers.mock import MockSpeechToTextProvider, MockTextToSpeechProvider
from app.modules.voice.protocol.types import SESSION_READY, SESSION_START
from app.modules.voice.ws.connection import VoiceConnectionHandler


class MockWebSocket:
    def __init__(self, incoming: list[str]) -> None:
        self._incoming: deque[str] = deque(incoming)
        self.sent: list[dict] = []
        self.client_state = WebSocketState.CONNECTED

    async def accept(self) -> None:
        return None

    async def receive_text(self) -> str:
        if not self._incoming:
            raise WebSocketDisconnect(code=1000)
        return self._incoming.popleft()

    async def send_json(self, data: dict) -> None:
        self.sent.append(data)

    async def close(self) -> None:
        self.client_state = WebSocketState.DISCONNECTED


@pytest.mark.asyncio
async def test_connection_handler_sends_ready_and_first_question() -> None:
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    question_id = uuid.uuid4()

    configured_session = SessionRecord(
        id=session_id,
        user_id=user_id,
        status=InterviewSessionStatus.CONFIGURED,
        interview_type=InterviewType.TECHNICAL,
        title="Voice test",
        config_snapshot={"difficulty": "mid"},
        question_count=0,
        resume_id=None,
        job_description_id=None,
        started_at=None,
        ended_at=None,
        end_reason=None,
    )
    orchestrator = AsyncMock(spec=InterviewOrchestrator)
    orchestrator.get_session = AsyncMock(return_value=configured_session)
    orchestrator.start = AsyncMock(
        return_value=QuestionResult(
            session=SessionRecord(
                id=session_id,
                user_id=user_id,
                status=InterviewSessionStatus.ACTIVE,
                interview_type=InterviewType.TECHNICAL,
                title="Voice test",
                config_snapshot={"difficulty": "mid"},
                question_count=1,
                resume_id=None,
                job_description_id=None,
                started_at=datetime.now(UTC),
                ended_at=None,
                end_reason=None,
            ),
            question=QuestionRecord(
                id=question_id,
                session_id=session_id,
                sequence_num=1,
                question_text="Describe your latest technical project.",
                topic_tag="technical",
                follow_up_intent=None,
                is_follow_up=False,
                asked_at=datetime.now(UTC),
                agent_metadata={},
            ),
            should_end_session=False,
        )
    )

    websocket = MockWebSocket(
        incoming=[
            json.dumps(
                {
                    "type": SESSION_START,
                    "payload": {"session_id": str(session_id)},
                    "request_id": "start-1",
                }
            ),
        ]
    )

    emitted: list[dict] = []

    async def emit(message: dict) -> None:
        emitted.append(message)
        await websocket.send_json(message)

    pipeline = VoicePipeline(
        orchestrator,
        MockSpeechToTextProvider(),
        MockTextToSpeechProvider(),
        emit=emit,
    )

    handler = VoiceConnectionHandler(websocket, session_id, user_id, orchestrator, pipeline)

    await handler.run()

    assert websocket.sent[0]["type"] == SESSION_READY
    assert any(message["type"] == "interviewer.response" for message in emitted)
    orchestrator.start.assert_awaited_once()
