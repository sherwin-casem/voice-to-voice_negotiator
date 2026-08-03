import pytest

from app.ai.schemas.evaluation.communication import CommunicationEvaluationOutput
from app.db.enums import AgentName, EvaluationRunStatus, InterviewType
from app.modules.evaluation.agents.judge import JudgeAgent
from app.modules.evaluation.agents.registry import build_specialist_evaluators
from app.modules.evaluation.factory import build_evaluation_service
from app.modules.evaluation.mock_llm import MockEvaluationLLMProvider
from app.modules.evaluation.schemas import EvaluationContext
from app.modules.evaluation.service import EvaluationService


def _sample_context() -> EvaluationContext:
    return EvaluationContext(
        interview_type=InterviewType.TECHNICAL,
        difficulty="senior",
        target_role="Staff Engineer",
        question_text="How would you debug elevated API latency?",
        answer_text="I would inspect metrics, traces, and recent deploys before narrowing to a bottleneck.",
        topic_tag="debugging",
    )


class FailingCommunicationLLM:
    async def generate_structured(self, messages, response_model, **kwargs):  # type: ignore[no-untyped-def]
        if response_model is CommunicationEvaluationOutput:
            raise RuntimeError("Simulated provider failure")
        return await MockEvaluationLLMProvider().generate_structured(
            messages,
            response_model,
            **kwargs,
        )


def _build_service(llm: object | None = None) -> EvaluationService:
    provider = llm or MockEvaluationLLMProvider()
    evaluators = build_specialist_evaluators(provider, model_id="mock-structured")  # type: ignore[arg-type]
    judge = JudgeAgent(provider, model_id="mock-structured")  # type: ignore[arg-type]
    return EvaluationService(evaluators, judge)


@pytest.mark.asyncio
async def test_evaluation_service_runs_specialists_in_parallel() -> None:
    service = build_evaluation_service()

    result = await service.evaluate(_sample_context())

    assert result.status == EvaluationRunStatus.COMPLETED
    assert len(result.agent_results) == 5
    assert result.judge_result is not None
    assert result.judge_result.succeeded
    assert len(result.successful_agents) >= 4
    assert all(item.latency_ms is not None for item in result.agent_results)
    assert all(item.model_id == "mock-structured" for item in result.successful_agents)


@pytest.mark.asyncio
async def test_evaluation_service_tolerates_single_agent_failure() -> None:
    service = _build_service(FailingCommunicationLLM())

    result = await service.evaluate(_sample_context())

    assert result.status == EvaluationRunStatus.COMPLETED
    communication = next(
        item for item in result.agent_results if item.agent_name == AgentName.COMMUNICATION_EVALUATION
    )
    assert communication.status == EvaluationRunStatus.FAILED
    assert communication.error_message is not None
    assert len(result.successful_agents) >= 3
    assert result.judge_result is not None
    assert result.judge_result.succeeded


@pytest.mark.asyncio
async def test_evaluation_service_records_execution_metadata() -> None:
    service = build_evaluation_service()

    result = await service.evaluate(_sample_context())
    metadata = result.successful_agents[0].to_metadata_dict()

    assert metadata["agent_name"]
    assert metadata["model_id"] == "mock-structured"
    assert metadata["prompt_version"] == "1.0"
    assert metadata["latency_ms"] is not None
    assert metadata["started_at"] is not None
    assert result.judge_result is not None
    assert result.judge_result.latency_ms is not None
