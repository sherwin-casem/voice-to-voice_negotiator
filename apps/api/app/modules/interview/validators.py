from app.ai.schemas.interviewer import InterviewerQuestionOutput


def normalize_question_output(
    output: InterviewerQuestionOutput,
    asked_topics: list[str],
) -> InterviewerQuestionOutput:
    """Apply deterministic post-processing so interviews avoid repeated topic tags."""
    if output.topic_tag and output.topic_tag in asked_topics:
        return output.model_copy(
            update={
                "topic_tag": f"{output.topic_tag}_followup",
                "question_text": (
                    "Let's explore a different angle. "
                    f"{output.question_text}"
                ),
            }
        )
    return output
