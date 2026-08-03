import base64
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.db.enums import InterviewSessionStatus, InterviewType
from app.modules.interview.orchestrator import QuestionResult
from app.modules.interview.schemas import QuestionRecord, SessionRecord
from app.modules.interview.orchestrator import InterviewOrchestrator
from app.modules.voice.pipeline.voice_pipeline import VoicePipeline
from app.modules.voice.providers.mock import MockSpeechToTextProvider, MockTextToSpeechProvider
from app.modules.voice.protocol.types import (
    AUDIO_OUTPUT,
    INTERVIEWER_RESPONSE,
    INTERVIEWER_THINKING,
    TRANSCRIPT_FINAL,
    TRANSCRIPT_PARTIAL,
)


@pytest.mark.asyncio
async def test_voice_pipeline_processes_turn_without_blocking_event_loop() -> None:
    emitted: list[dict] = []

    async def emit(message: dict) -> None:
        emitted.append(message)

    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    question_id = uuid.uuid4()
    next_question_id = uuid.uuid4()

    orchestrator = AsyncMock(spec=InterviewOrchestrator)
    orchestrator.submit_answer = AsyncMock()
    orchestrator.ask_next_question = AsyncMock(
        return_value=QuestionResult(
            session=SessionRecord(
                id=session_id,
                user_id=user_id,
                status=InterviewSessionStatus.ACTIVE,
                interview_type=InterviewType.BEHAVIORAL,
                title="Test",
                config_snapshot={},
                question_count=2,
                resume_id=None,
                job_description_id=None,
                started_at=datetime.now(UTC),
                ended_at=None,
                end_reason=None,
            ),
            question=QuestionRecord(
                id=next_question_id,
                session_id=session_id,
                sequence_num=2,
                question_text="Tell me more about that project.",
                topic_tag="follow_up",
                follow_up_intent="Probe impact",
                is_follow_up=True,
                asked_at=datetime.now(UTC),
                agent_metadata={},
            ),
            should_end_session=False,
        )
    )

    pipeline = VoicePipeline(
        orchestrator,
        MockSpeechToTextProvider(),
        MockTextToSpeechProvider(),
        emit=emit,
    )
    pipeline.set_current_question(question_id)
    pipeline.configure_audio_format(16000, "pcm_s16le", 1)

    audio_b64 = base64.b64encode(b"candidate audio bytes").decode("ascii")
    await pipeline.append_audio_input(0, audio_b64)
    await pipeline.process_speech_end(session_id=session_id, user_id=user_id, request_id="req-1")

    event_types = [message["type"] for message in emitted]
    assert TRANSCRIPT_PARTIAL in event_types
    assert TRANSCRIPT_FINAL in event_types
    assert INTERVIEWER_THINKING in event_types
    assert INTERVIEWER_RESPONSE in event_types
    assert AUDIO_OUTPUT in event_types

    orchestrator.submit_answer.assert_awaited_once()
    orchestrator.ask_next_question.assert_awaited_once()


@pytest.mark.asyncio
async def test_voice_pipeline_streams_multiple_audio_output_chunks() -> None:
    emitted: list[dict] = []

    async def emit(message: dict) -> None:
        emitted.append(message)

    pipeline = VoicePipeline(
        AsyncMock(spec=InterviewOrchestrator),
        MockSpeechToTextProvider(),
        MockTextToSpeechProvider(),
        emit=emit,
    )

    await pipeline.deliver_interviewer_turn(
        session_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        question_id=uuid.uuid4(),
        text="This is a longer interviewer response for streaming TTS output.",
        topic_tag="intro",
        should_end_session=False,
    )

    audio_events = [message for message in emitted if message["type"] == AUDIO_OUTPUT]
    assert len(audio_events) >= 1
    assert audio_events[-1]["payload"]["is_final"] is True
