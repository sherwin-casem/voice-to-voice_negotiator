import pytest

from app.ai.prompts.interviewer.v1 import build_interviewer_messages
from app.ai.schemas.interviewer import InterviewerContext, PriorTurn
from app.db.enums import InterviewType


def test_build_interviewer_messages_includes_context() -> None:
    context = InterviewerContext(
        interview_type=InterviewType.TECHNICAL,
        difficulty="senior",
        target_role="Backend Engineer",
        company_context="Payments startup",
        resume_summary="10 years Python experience",
        job_description_summary="Build scalable APIs",
        prior_turns=[
            PriorTurn(
                sequence_num=1,
                question_text="Tell me about caching.",
                answer_text="We used Redis.",
                topic_tag="caching",
            )
        ],
        question_number=2,
        max_questions=5,
        asked_topics=["caching"],
    )

    messages = build_interviewer_messages(context)

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "technical" in messages[0]["content"].lower()
    assert "Backend Engineer" in messages[0]["content"]
    assert "caching" in messages[0]["content"]
    assert "Redis" in messages[1]["content"]


def test_build_interviewer_messages_handles_opening_turn() -> None:
    context = InterviewerContext(
        interview_type=InterviewType.BEHAVIORAL,
        difficulty="mid",
        question_number=1,
    )

    messages = build_interviewer_messages(context)

    assert "None yet" in messages[1]["content"]
