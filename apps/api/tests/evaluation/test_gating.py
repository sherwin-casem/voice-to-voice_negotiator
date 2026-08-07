import pytest

from app.db.enums import EvaluationScope, InterviewType
from app.modules.evaluation.gating import (
    should_run_behavioral,
    should_run_communication,
    should_run_hiring_manager,
    should_run_relevance,
    should_run_technical,
)


@pytest.mark.parametrize("interview_type", list(InterviewType))
def test_communication_always_runs(interview_type: InterviewType) -> None:
    should_run, reason = should_run_communication(interview_type)
    assert should_run is True
    assert reason is None


@pytest.mark.parametrize("interview_type", list(InterviewType))
def test_relevance_always_runs(interview_type: InterviewType) -> None:
    should_run, reason = should_run_relevance(interview_type)
    assert should_run is True
    assert reason is None


def test_hiring_manager_runs_for_session_scope() -> None:
    should_run, reason = should_run_hiring_manager(EvaluationScope.SESSION)
    assert should_run is True
    assert reason is None


def test_hiring_manager_skipped_for_answer_scope() -> None:
    should_run, reason = should_run_hiring_manager(EvaluationScope.ANSWER)
    assert should_run is False
    assert reason is not None


@pytest.mark.parametrize(
    ("interview_type", "expected"),
    [
        (InterviewType.BEHAVIORAL, False),
        (InterviewType.HR, False),
        (InterviewType.LEADERSHIP, False),
        (InterviewType.TECHNICAL, True),
        (InterviewType.SYSTEM_DESIGN, True),
    ],
)
def test_technical_gating(interview_type: InterviewType, expected: bool) -> None:
    should_run, reason = should_run_technical(interview_type)
    assert should_run is expected
    if not expected:
        assert reason is not None


@pytest.mark.parametrize(
    ("interview_type", "expected"),
    [
        (InterviewType.TECHNICAL, False),
        (InterviewType.SYSTEM_DESIGN, False),
        (InterviewType.BEHAVIORAL, True),
        (InterviewType.HR, True),
        (InterviewType.LEADERSHIP, True),
    ],
)
def test_behavioral_gating(interview_type: InterviewType, expected: bool) -> None:
    should_run, reason = should_run_behavioral(interview_type)
    assert should_run is expected
    if not expected:
        assert reason is not None
