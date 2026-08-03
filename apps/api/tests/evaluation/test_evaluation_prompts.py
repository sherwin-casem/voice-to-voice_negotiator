from app.ai.prompts.evaluation.communication.v1 import build_communication_messages
from app.db.enums import InterviewType
from app.modules.evaluation.schemas import EvaluationContext


def test_communication_prompt_includes_rubric_and_context() -> None:
    context = EvaluationContext(
        interview_type=InterviewType.TECHNICAL,
        difficulty="senior",
        target_role="Backend Engineer",
        company_context="Fintech",
        resume_summary="Built payment APIs",
        job_description_summary="Design scalable backend systems",
        question_text="Explain your approach to caching.",
        answer_text="We used Redis with TTL-based invalidation and cache-aside reads.",
        topic_tag="caching",
    )

    messages = build_communication_messages(context)

    assert messages[0]["role"] == "system"
    assert "clarity" in messages[0]["content"].lower()
    assert "Backend Engineer" in messages[0]["content"]
    assert "Redis" in messages[1]["content"]
