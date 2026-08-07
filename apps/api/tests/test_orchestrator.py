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


@pytest.mark.asyncio
async def test_end_session_with_answers_enters_completing(
    orchestrator: InterviewOrchestrator,
    repository: AsyncMock,
) -> None:
    """Sessions with answered questions hand off to the evaluation pipeline."""
    interview_session = _make_interview_session(
        status=InterviewSessionStatus.ACTIVE,
        question_count=1,
    )
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
    repository.update_session_status.return_value = _session_record(
        status=InterviewSessionStatus.COMPLETING,
    )

    result = await orchestrator.end_session(
        interview_session.id,
        interview_session.user_id,
        reason="user_ended",
    )

    repository.update_session_status.assert_awaited_once_with(
        interview_session,
        InterviewSessionStatus.COMPLETING,
        end_reason="user_ended",
    )
    assert result.status == InterviewSessionStatus.COMPLETING


@pytest.mark.asyncio
async def test_end_session_while_completing_is_noop(
    orchestrator: InterviewOrchestrator,
    repository: AsyncMock,
) -> None:
    """A second end request must not race the in-flight evaluation."""
    interview_session = _make_interview_session(status=InterviewSessionStatus.COMPLETING)
    repository.get_session_for_user.return_value = interview_session

    result = await orchestrator.end_session(
        interview_session.id,
        interview_session.user_id,
        reason="user_ended",
    )

    repository.update_session_status.assert_not_awaited()
    assert result.status == InterviewSessionStatus.COMPLETING


@pytest.mark.asyncio
async def test_submit_answer_persists_answer(
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
    answer_record = AnswerRecord(
        id=uuid.uuid4(),
        session_id=interview_session.id,
        question_id=question.id,
        answer_text="My answer",
        answered_at=datetime.now(UTC),
        duration_ms=12000,
        word_count=2,
    )
    repository.add_answer.return_value = answer_record

    result = await orchestrator.submit_answer(
        interview_session.id,
        interview_session.user_id,
        question.id,
        answer_text="My answer",
        duration_ms=12000,
    )

    repository.add_answer.assert_awaited_once()
    assert result.answer.answer_text == "My answer"


@pytest.mark.asyncio
async def test_full_interview_lifecycle(
    orchestrator: InterviewOrchestrator,
    repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    created = _session_record(status=InterviewSessionStatus.CREATED)
    configured = _session_record(status=InterviewSessionStatus.CONFIGURED)
    configured = SessionRecord(
        **{**configured.__dict__, "config_snapshot": {"interview_type": "behavioral", "difficulty": "mid", "max_questions": 2}},
    )

    interview_session = _make_interview_session(
        status=InterviewSessionStatus.CREATED,
        config_snapshot={"interview_type": "behavioral", "difficulty": "mid", "max_questions": 2},
    )
    interview_session.user_id = user_id

    repository.create_session.return_value = created
    repository.get_session_for_user.side_effect = [
        interview_session,
        _make_interview_session(
            status=InterviewSessionStatus.CONFIGURED,
            config_snapshot=interview_session.config_snapshot,
        ),
        _make_interview_session(
            status=InterviewSessionStatus.CONFIGURED,
            config_snapshot=interview_session.config_snapshot,
        ),
    ]
    repository.configure_session.return_value = configured
    repository.get_context_summaries.return_value = MagicMock(
        resume_summary="Built APIs at scale",
        job_description_summary="Senior backend role",
        company_name="Acme",
    )
    repository.add_question.side_effect = [
        _question_record(interview_session.id, sequence_num=1),
        _question_record(interview_session.id, sequence_num=2),
    ]
    repository.update_session_status.return_value = _session_record(status=InterviewSessionStatus.COMPLETED)

    session = await orchestrator.create_session(user_id, title="Practice")
    assert session.status == InterviewSessionStatus.CREATED

    configured_session = await orchestrator.configure_session(
        interview_session.id,
        user_id,
        SessionConfigInput(
            interview_type=InterviewType.BEHAVIORAL,
            difficulty="mid",
            target_role="Backend Engineer",
            company_context="High-growth startup",
            max_questions=2,
        ),
    )
    assert configured_session.status == InterviewSessionStatus.CONFIGURED

    active_session = _make_interview_session(
        status=InterviewSessionStatus.CONFIGURED,
        config_snapshot=interview_session.config_snapshot,
    )
    active_session.user_id = user_id
    active_session.questions = []
    repository.get_session_for_user.side_effect = None
    repository.get_session_for_user.return_value = active_session

    first_question = await orchestrator.start(interview_session.id, user_id)
    assert first_question.question.sequence_num == 1

    q1 = InterviewQuestion(
        id=first_question.question.id,
        session_id=interview_session.id,
        sequence_num=1,
        question_text=first_question.question.question_text,
        asked_at=datetime.now(UTC),
        is_follow_up=False,
        agent_metadata={},
    )
    q1.answer = None
    active_after_q1 = _make_interview_session(
        status=InterviewSessionStatus.ACTIVE,
        question_count=1,
        config_snapshot=interview_session.config_snapshot,
    )
    active_after_q1.user_id = user_id
    active_after_q1.questions = [q1]
    repository.get_session_for_user.return_value = active_after_q1
    repository.get_latest_question.return_value = q1
    repository.add_answer.return_value = AnswerRecord(
        id=uuid.uuid4(),
        session_id=interview_session.id,
        question_id=q1.id,
        answer_text="STAR answer",
        answered_at=datetime.now(UTC),
        duration_ms=30000,
        word_count=50,
    )

    answer_result = await orchestrator.submit_answer(
        interview_session.id,
        user_id,
        q1.id,
        answer_text="STAR answer",
    )
    assert answer_result.answer.answer_text == "STAR answer"

    q1.answer = MagicMock(answer_text="STAR answer")
    repository.add_question.return_value = _question_record(interview_session.id, sequence_num=2)
    second_question = await orchestrator.ask_next_question(interview_session.id, user_id)
    assert second_question.question.sequence_num == 2

    ended = await orchestrator.end_session(interview_session.id, user_id, reason="user_ended")
    assert ended.status == InterviewSessionStatus.COMPLETED
