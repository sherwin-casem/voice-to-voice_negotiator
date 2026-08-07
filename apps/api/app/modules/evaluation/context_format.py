from app.ai.prompts.fencing import fence_untrusted
from app.modules.evaluation.schemas import ConversationTurn, EvaluationContext


def format_prior_turns(turns: list[ConversationTurn]) -> str:
    if not turns:
        return "No prior turns."

    lines: list[str] = []
    for turn in turns:
        lines.append(
            f"Q{turn.sequence_num} [{turn.topic_tag or 'general'}]: {turn.question_text}\n"
            f"A{turn.sequence_num}: {turn.answer_text}"
        )
    return fence_untrusted("\n\n".join(lines), "prior answers")


def format_evaluation_context(context: EvaluationContext) -> dict[str, str]:
    return {
        "interview_type": context.interview_type.value,
        "difficulty": context.difficulty,
        "target_role": context.target_role or "Not specified",
        "company_context": context.company_context or "Not specified",
        "resume_summary": _fenced_optional(context.resume_summary, "resume summary"),
        "job_description_summary": _fenced_optional(
            context.job_description_summary, "job description summary"
        ),
        "candidate_skills": _format_list(context.candidate_skills),
        "relevant_experience": _format_list(context.relevant_experience),
        "role_responsibilities": _format_list(context.role_responsibilities),
        "technical_focus_areas": _format_list(context.technical_focus_areas),
        "behavioral_focus_areas": _format_list(context.behavioral_focus_areas),
        "evaluation_rubric_hints": _format_list(context.evaluation_rubric_hints),
        "question_text": context.question_text,
        "answer_text": fence_untrusted(context.answer_text, "candidate answer"),
        "topic_tag": context.topic_tag or "general",
        "prior_turns": format_prior_turns(context.prior_turns),
        "scope": context.scope.value,
    }


def _format_list(values: list[str], empty_label: str = "Not provided") -> str:
    if not values:
        return empty_label
    return ", ".join(values)


def _fenced_optional(value: str | None, label: str) -> str:
    if not value:
        return "Not provided"
    return fence_untrusted(value, label)
