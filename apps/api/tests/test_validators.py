from app.ai.schemas.interviewer import InterviewerQuestionOutput
from app.modules.interview.validators import normalize_question_output


def test_normalize_question_output_rewrites_duplicate_topic() -> None:
    output = InterviewerQuestionOutput(
        question_text="Tell me more about caching.",
        topic_tag="caching",
        is_follow_up=True,
        should_end_session=False,
        difficulty_adjustment="same",
        prompt_version="1.0",
    )

    normalized = normalize_question_output(output, asked_topics=["caching"])

    assert normalized.topic_tag == "caching_followup"
    assert "different angle" in normalized.question_text.lower()


def test_normalize_question_output_keeps_unique_topic() -> None:
    output = InterviewerQuestionOutput(
        question_text="How do you handle conflict?",
        topic_tag="conflict",
        is_follow_up=False,
        should_end_session=False,
        difficulty_adjustment="same",
        prompt_version="1.0",
    )

    normalized = normalize_question_output(output, asked_topics=["motivation"])

    assert normalized == output
