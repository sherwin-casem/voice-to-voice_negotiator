import pytest

from app.db.enums import InterviewSessionStatus, InterviewType
from app.modules.interview.state_machine import (
    assert_transition,
    can_transition,
    is_terminal,
)


def test_created_to_configured_is_allowed() -> None:
    assert can_transition(InterviewSessionStatus.CREATED, InterviewSessionStatus.CONFIGURED)


def test_active_to_completed_is_allowed() -> None:
    assert can_transition(InterviewSessionStatus.ACTIVE, InterviewSessionStatus.COMPLETED)


def test_created_to_active_is_not_allowed() -> None:
    assert not can_transition(InterviewSessionStatus.CREATED, InterviewSessionStatus.ACTIVE)


def test_assert_transition_raises_for_invalid_move() -> None:
    with pytest.raises(ValueError, match="Cannot transition"):
        assert_transition(InterviewSessionStatus.CREATED, InterviewSessionStatus.ACTIVE)


def test_completed_is_terminal() -> None:
    assert is_terminal(InterviewSessionStatus.COMPLETED)
    assert not is_terminal(InterviewSessionStatus.ACTIVE)


@pytest.mark.parametrize(
    "interview_type",
    [
        InterviewType.BEHAVIORAL,
        InterviewType.TECHNICAL,
        InterviewType.SYSTEM_DESIGN,
        InterviewType.LEADERSHIP,
        InterviewType.HR,
    ],
)
def test_all_interview_types_exist(interview_type: InterviewType) -> None:
    assert interview_type.value in {
        "behavioral",
        "technical",
        "system_design",
        "leadership",
        "hr",
    }
