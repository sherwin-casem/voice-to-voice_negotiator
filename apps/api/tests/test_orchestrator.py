import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictError, InvalidStateError
from app.db.enums import InterviewSessionStatus, InterviewType
from app.db.models.interview import InterviewQuestion, InterviewSession
from app.modules.interview.interviewer_agent import InterviewerAgent, MockInterviewerLLMProvider
from app.modules.interview.orchestrator import InterviewOrchestrator
from app.modules.interview.schemas import (
    AnswerRecord,
    QuestionRecord,
    SessionConfigInput,
    SessionRecord,
)
from app.modules.interview.repository import InterviewRepository


def _session_record(
    status: InterviewSessionStatus = InterviewSessionStatus.CREATED,
) -> SessionRecord:
    return SessionRecord(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=status,
        interview_type=InterviewType.BEHAVIORAL,
        title="Mock interview",
        config_snapshot={},
        question_count=0,
        resume_id=None,
        job_description_id=None,
        started_at=None,
        ended_at=None,
        end_reason=None,
    )


def _question_record(session_id: uuid.UUID, sequence_num: int = 1) -> QuestionRecord:
    return QuestionRecord(
        id=uuid.uuid4(),
        session_id=session_id,
        sequence_num=sequence_num,
        question_text="Tell me about yourself.",
        topic_tag="introduction",
        follow_up_intent=None,
        is_follow_up=False,
        asked_at=datetime.now(UTC),
        agent_metadata={"prompt_version": "1.0"},
    )


def _make_interview_session(
    *,
    status: InterviewSessionStatus = InterviewSessionStatus.CONFIGURED,
    question_count: int = 0,
    config_snapshot: dict | None = None,
) -> InterviewSession:
    session = InterviewSession(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        interview_type=InterviewType.BEHAVIORAL,
        status=status,
        config_snapshot=config_snapshot
        or {
            "interview_type": "behavioral",
            "difficulty": "mid",
            "target_role": "Engineer",
            "max_questions": 3,
        },
        question_count=question_count,
    )
    session.questions = []
    session.resume = None
    session.job_description = None
    return session


@pytest.fixture
def repository() -> AsyncMock:
    repo = AsyncMock(spec=InterviewRepository)
    repo._to_session_record = InterviewRepository._to_session_record
    repo.to_session_record = InterviewRepository.to_session_record
    return repo


@pytest.fixture
def orchestrator(repository: AsyncMock) -> InterviewOrchestrator:
    agent = InterviewerAgent(MockInterviewerLLMProvider())
    return InterviewOrchestrator(repository, agent)


@pytest.mark.asyncio
async def test_create_session_delegates_to_repository(orchestrator: InterviewOrchestrator, repository: AsyncMock) -> None:
    user_id = uuid.uuid4()
    expected = _session_record()
    repository.create_session.return_value = expected

    result = await orchestrator.create_session(user_id, title="Practice")

    repository.create_session.assert_awaited_once_with(user_id, title="Practice")
    assert result == expected


@pytest.mark.asyncio
async def test_configure_session_requires_created_status(
    orchestrator: InterviewOrchestrator,
    repository: AsyncMock,
) -> None:
    active_session = _make_interview_session(status=InterviewSessionStatus.ACTIVE)
    repository.get_session_for_user.return_value = active_session

    with pytest.raises(InvalidStateError):
        await orchestrator.configure_session(
            active_session.id,
            active_session.user_id,
            SessionConfigInput(
                interview_type=InterviewType.TECHNICAL,
                difficulty="senior",
            ),
        )


@pytest.mark.asyncio
async def test_start_transitions_to_active_and_returns_question(
    orchestrator: InterviewOrchestrator,
    repository: AsyncMock,
) -> None:
    interview_session = _make_interview_session()
    repository.get_session_for_user.return_value = interview_session
    repository.get_context_summaries.return_value = MagicMock(
        resume_summary=None,
        job_description_summary=None,
        company_name=None,
    )
    repository.add_question.return_value = _question_record(interview_session.id)

    result = await orchestrator.start(interview_session.id, interview_session.user_id)

    repository.update_session_status.assert_awaited_once()
    repository.add_question.assert_awaited_once()
    assert result.question.sequence_num == 1


@pytest.mark.asyncio
async def test_submit_answer_rejects_already_answered_question(
    orchestrator: InterviewOrchestrator,
    repository: AsyncMock,
) -> None:
    interview_session = _make_interview_session(status=InterviewSessionStatus.ACTIVE, question_count=1)
    question = InterviewQuestion(
        id=uuid.uuid4(),
        session_id=interview_session.id,
        sequence_num=1,
        question_text="Question?",
        asked_at=datetime.now(UTC),
        is_follow_up=False,
        agent_metadata={},
    )
    question.answer = MagicMock()
    interview_session.questions = [question]
    repository.get_session_for_user.return_value = interview_session
    repository.get_latest_question.return_value = question

    with pytest.raises(ConflictError):
        await orchestrator.submit_answer(
            interview_session.id,
            interview_session.user_id,
            question.id,
            answer_text="My answer",
        )


@pytest.mark.asyncio
async def test_ask_next_question_requires_answered_current_question(
    orchestrator: InterviewOrchestrator,
    repository: AsyncMock,
) -> None:
    interview_session = _make_interview_session(status=InterviewSessionStatus.ACTIVE, question_count=1)
    question = InterviewQuestion(
        id=uuid.uuid4(),
        session_id=interview_session.id,
        sequence_num=1,
        question_text="Question?",
        asked_at=datetime.now(UTC),
        is_follow_up=False,
        agent_metadata={},
    )
    question.answer = None
    interview_session.questions = [question]
    repository.get_session_for_user.return_value = interview_session
    repository.get_latest_question.return_value = question

    with pytest.raises(ConflictError, match="Answer the current question"):
        await orchestrator.ask_next_question(interview_session.id, interview_session.user_id)


@pytest.mark.asyncio
async def test_end_session_from_active_sets_completed(
    orchestrator: InterviewOrchestrator,
    repository: AsyncMock,
) -> None:
    interview_session = _make_interview_session(status=InterviewSessionStatus.ACTIVE)
    repository.get_session_for_user.return_value = interview_session
    completed = _session_record(status=InterviewSessionStatus.COMPLETED)
    repository.update_session_status.return_value = completed

    result = await orchestrator.end_session(
        interview_session.id,
        interview_session.user_id,
        reason="user_ended",
    )

    repository.update_session_status.assert_awaited_once()
    assert result.status == InterviewSessionStatus.COMPLETED
