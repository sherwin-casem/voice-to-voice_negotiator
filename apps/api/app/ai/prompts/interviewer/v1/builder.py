from pathlib import Path

from app.ai.schemas.interviewer import InterviewerContext
from app.db.enums import InterviewType

PROMPT_VERSION = "1.0"
_TEMPLATES_DIR = Path(__file__).parent / "templates"

_TYPE_GUIDANCE: dict[InterviewType, str] = {
    InterviewType.BEHAVIORAL: (
        "Focus on past behavior, STAR stories, teamwork, conflict, ownership, and impact."
    ),
    InterviewType.TECHNICAL: (
        "Focus on fundamentals, problem solving, coding concepts, debugging, and trade-offs."
    ),
    InterviewType.SYSTEM_DESIGN: (
        "Focus on architecture, scalability, reliability, APIs, data modeling, and bottlenecks."
    ),
    InterviewType.LEADERSHIP: (
        "Focus on leading teams, vision, mentoring, cross-functional influence, and decision making."
    ),
    InterviewType.HR: (
        "Focus on motivation, culture fit, career goals, communication, and role alignment."
    ),
}

_TYPE_LABELS: dict[InterviewType, str] = {
    InterviewType.BEHAVIORAL: "behavioral",
    InterviewType.TECHNICAL: "technical",
    InterviewType.SYSTEM_DESIGN: "system design",
    InterviewType.LEADERSHIP: "leadership",
    InterviewType.HR: "HR",
}


def _load_template(name: str) -> str:
    return (_TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _format_prior_turns(context: InterviewerContext) -> str:
    if not context.prior_turns:
        return "None yet. This is the opening question."

    lines: list[str] = []
    for turn in context.prior_turns:
        answer = turn.answer_text or "(no answer recorded)"
        lines.append(
            f"Q{turn.sequence_num} [{turn.topic_tag or 'general'}]: {turn.question_text}\n"
            f"A{turn.sequence_num}: {answer}"
        )
    return "\n\n".join(lines)


def build_interviewer_messages(context: InterviewerContext) -> list[dict[str, str]]:
    system_template = _load_template("system.txt")
    user_template = _load_template("user.txt")

    type_guidance = _TYPE_GUIDANCE[context.interview_type]
    max_questions_line = (
        f" of {context.max_questions}" if context.max_questions is not None else ""
    )

    system_content = system_template.format(
        interview_type_label=_TYPE_LABELS[context.interview_type],
        interview_type=context.interview_type.value,
        difficulty=context.difficulty,
        target_role=context.target_role or "Not specified",
        company_context=context.company_context or "Not specified",
        resume_summary=context.resume_summary or "Not provided",
        job_description_summary=context.job_description_summary or "Not provided",
        asked_topics=", ".join(context.asked_topics) if context.asked_topics else "None",
        question_number=context.question_number,
        max_questions_line=max_questions_line,
    )
    system_content = f"{system_content.strip()}\n\nType-specific guidance:\n{type_guidance}"

    user_content = user_template.format(
        prior_turns=_format_prior_turns(context),
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
