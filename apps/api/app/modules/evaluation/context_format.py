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
    return "\n\n".join(lines)


def format_evaluation_context(context: EvaluationContext) -> dict[str, str]:
    return {
        "interview_type": context.interview_type.value,
        "difficulty": context.difficulty,
        "target_role": context.target_role or "Not specified",
        "company_context": context.company_context or "Not specified",
        "resume_summary": context.resume_summary or "Not provided",
        "job_description_summary": context.job_description_summary or "Not provided",
        "question_text": context.question_text,
        "answer_text": context.answer_text,
        "topic_tag": context.topic_tag or "general",
        "prior_turns": format_prior_turns(context.prior_turns),
        "scope": context.scope.value,
    }
