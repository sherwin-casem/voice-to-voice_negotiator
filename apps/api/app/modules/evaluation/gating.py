from app.db.enums import InterviewType

_TECHNICAL_TYPES = frozenset({InterviewType.TECHNICAL, InterviewType.SYSTEM_DESIGN})
_BEHAVIORAL_TYPES = frozenset(
    {InterviewType.BEHAVIORAL, InterviewType.LEADERSHIP, InterviewType.HR},
)


def should_run_technical(interview_type: InterviewType) -> tuple[bool, str | None]:
    if interview_type in _BEHAVIORAL_TYPES:
        return False, f"Technical evaluation is not applicable for {interview_type.value} interviews"
    return True, None


def should_run_behavioral(interview_type: InterviewType) -> tuple[bool, str | None]:
    if interview_type in _TECHNICAL_TYPES:
        return False, f"Behavioral evaluation is de-emphasized for {interview_type.value} interviews"
    return True, None


def should_run_communication(_interview_type: InterviewType) -> tuple[bool, str | None]:
    return True, None


def should_run_relevance(_interview_type: InterviewType) -> tuple[bool, str | None]:
    return True, None


def should_run_hiring_manager(_interview_type: InterviewType) -> tuple[bool, str | None]:
    return True, None
