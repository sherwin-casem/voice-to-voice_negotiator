from app.db.enums import InterviewSessionStatus

ALLOWED_TRANSITIONS: dict[InterviewSessionStatus, set[InterviewSessionStatus]] = {
    InterviewSessionStatus.CREATED: {InterviewSessionStatus.CONFIGURED},
    InterviewSessionStatus.CONFIGURED: {InterviewSessionStatus.ACTIVE},
    InterviewSessionStatus.ACTIVE: {
        InterviewSessionStatus.COMPLETING,
        InterviewSessionStatus.COMPLETED,
        InterviewSessionStatus.ABANDONED,
    },
    InterviewSessionStatus.COMPLETING: {
        InterviewSessionStatus.COMPLETED,
        InterviewSessionStatus.EVALUATION_FAILED,
    },
}


def can_transition(
    current: InterviewSessionStatus,
    target: InterviewSessionStatus,
) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(
    current: InterviewSessionStatus,
    target: InterviewSessionStatus,
) -> None:
    if not can_transition(current, target):
        raise ValueError(f"Cannot transition from {current.value} to {target.value}")


def is_terminal(status: InterviewSessionStatus) -> bool:
    return status in {
        InterviewSessionStatus.COMPLETED,
        InterviewSessionStatus.ABANDONED,
        InterviewSessionStatus.EVALUATION_FAILED,
    }


def requires_configuration(status: InterviewSessionStatus) -> bool:
    return status == InterviewSessionStatus.CONFIGURED


def requires_active(status: InterviewSessionStatus) -> bool:
    return status == InterviewSessionStatus.ACTIVE
