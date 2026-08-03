import pytest

from app.ai.schemas.evaluation.communication import CommunicationEvaluationOutput
from app.db.enums import AgentName, EvaluationRunStatus, InterviewType
from app.modules.evaluation.agents.registry import build_specialist_evaluators
from app.modules.evaluation.mock_llm import MockEvaluationLLMProvider
from app.modules.evaluation.schemas import EvaluationContext


def _sample_context(interview_type: InterviewType = InterviewType.BEHAVIORAL) -> EvaluationContext:
    return EvaluationContext(
        interview_type=interview_type,
        difficulty="mid",
        target_role="Backend Engineer",
        company_context="Series B startup",
        resume_summary="5 years building APIs",
        job_description_summary="Own backend services and mentor juniors",
        question_text="Tell me about a challenging project.",
        answer_text="I led a migration from monolith to services with measurable latency gains.",
        topic_tag="project_leadership",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("agent_name", "interview_type"),
    [
        (AgentName.COMMUNICATION_EVALUATION, InterviewType.BEHAVIORAL),
        (AgentName.TECHNICAL_EVALUATION, InterviewType.TECHNICAL),
        (AgentName.BEHAVIORAL_EVALUATION, InterviewType.BEHAVIORAL),
        (AgentName.RELEVANCE_EVALUATION, InterviewType.LEADERSHIP),
        (AgentName.HIRING_MANAGER_EVALUATION, InterviewType.HR),
    ],
)
async def test_specialist_evaluators_return_structured_output(
    agent_name: AgentName,
    interview_type: InterviewType,
) -> None:
    evaluators = build_specialist_evaluators(MockEvaluationLLMProvider(), model_id="mock-structured")
    evaluator = next(item for item in evaluators if item.agent_name == agent_name)

    result = await evaluator.evaluate(_sample_context(interview_type))

    assert result.status == EvaluationRunStatus.COMPLETED
    assert result.output is not None
    assert result.prompt_version == "1.0"
    assert result.model_id == "mock-structured"
    assert result.latency_ms is not None
    assert result.started_at is not None
    assert result.completed_at is not None


@pytest.mark.asyncio
async def test_technical_evaluator_skips_for_behavioral_interview() -> None:
    evaluators = build_specialist_evaluators(MockEvaluationLLMProvider(), model_id="mock-structured")
    technical = next(
        item for item in evaluators if item.agent_name == AgentName.TECHNICAL_EVALUATION
    )

    result = await technical.evaluate(_sample_context(InterviewType.BEHAVIORAL))

    assert result.status == EvaluationRunStatus.SKIPPED
    assert result.skipped is True
    assert result.skip_reason is not None
    assert result.output is None


@pytest.mark.asyncio
async def test_communication_output_schema_shape() -> None:
    evaluators = build_specialist_evaluators(MockEvaluationLLMProvider(), model_id="mock-structured")
    communication = next(
        item for item in evaluators if item.agent_name == AgentName.COMMUNICATION_EVALUATION
    )

    result = await communication.evaluate(_sample_context())
    assert isinstance(result.output, CommunicationEvaluationOutput)
    assert result.output.dimensions.clarity.score >= 0
