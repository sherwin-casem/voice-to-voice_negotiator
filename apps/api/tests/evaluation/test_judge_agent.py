import pytest

from app.ai.schemas.evaluation.judge import JudgeEvaluationOutput
from app.db.enums import AgentName, EvaluationRunStatus, InterviewType
from app.modules.evaluation.agents.judge import JudgeAgent
from app.modules.evaluation.mock_llm import MockEvaluationLLMProvider
from tests.evaluation.helpers import (
    behavioral_output,
    build_specialist_results,
    communication_output,
    hiring_manager_output,
    relevance_output,
    sample_context,
    technical_output,
)


@pytest.fixture
def judge() -> JudgeAgent:
    return JudgeAgent(MockEvaluationLLMProvider(), model_id="mock-structured")


@pytest.mark.asyncio
async def test_judge_resolves_conflicting_evaluations(judge: JudgeAgent) -> None:
    context = sample_context(InterviewType.TECHNICAL)
    results = build_specialist_results(
        communication=communication_output(clarity=9.5, tone=9.0),
        relevance=relevance_output(question_responsiveness=4.0),
        technical=technical_output(depth=8.5, accuracy=8.0),
    )

    result = await judge.judge(context, results)
    output = result.output
    assert isinstance(output, JudgeEvaluationOutput)
    assert result.status == EvaluationRunStatus.COMPLETED
    assert output.conflict_resolutions
    assert output.overall_score <= 90


@pytest.mark.asyncio
async def test_judge_handles_missing_evaluator_results(judge: JudgeAgent) -> None:
    context = sample_context(InterviewType.BEHAVIORAL)
    results = build_specialist_results(
        skipped_agents={AgentName.TECHNICAL_EVALUATION: "Not applicable for behavioral"},
    )

    result = await judge.judge(context, results)
    output = result.output
    assert isinstance(output, JudgeEvaluationOutput)
    assert output.dimension_scores.technical is None
    assert output.overall_score > 0


@pytest.mark.asyncio
async def test_judge_handles_failed_evaluator(judge: JudgeAgent) -> None:
    context = sample_context(InterviewType.TECHNICAL)
    results = build_specialist_results(failed_agents={AgentName.COMMUNICATION_EVALUATION})

    result = await judge.judge(context, results)
    output = result.output
    assert isinstance(output, JudgeEvaluationOutput)
    assert result.status == EvaluationRunStatus.COMPLETED
    # Failed communication specialist is excluded from scoring, not neutralized.
    assert output.dimension_scores.communication is None
    assert "communication" not in output.weights_applied


@pytest.mark.asyncio
async def test_judge_strong_technical_answer(judge: JudgeAgent) -> None:
    context = sample_context(
        InterviewType.TECHNICAL,
        answer_text=(
            "I would inspect latency metrics, distributed traces, and recent deploys, "
            "then isolate the slow dependency and validate with load tests."
        ),
    )
    results = build_specialist_results(
        communication=communication_output(clarity=9.0, structure=9.0, conciseness=8.5, confidence=9.0, tone=9.0),
        technical=technical_output(depth=9.0, accuracy=9.5, problem_solving=9.0, trade_off_awareness=8.5),
        relevance=relevance_output(
            role_alignment=9.0,
            jd_alignment=8.5,
            question_responsiveness=9.5,
            context_usage=8.5,
        ),
        hiring_manager=hiring_manager_output(role_readiness=8.5, risk_assessment=8.0),
    )

    result = await judge.judge(context, results)
    output = result.output
    assert isinstance(output, JudgeEvaluationOutput)
    assert output.overall_score >= 85
    assert output.strengths
    assert output.evidence
    assert output.evidence[0].quote


@pytest.mark.asyncio
async def test_judge_weak_behavioral_answer(judge: JudgeAgent) -> None:
    context = sample_context(
        InterviewType.BEHAVIORAL,
        answer_text="I guess I would try to handle it somehow.",
    )
    results = build_specialist_results(
        communication=communication_output(clarity=3.0, structure=3.5, conciseness=4.0, confidence=3.0, tone=4.0),
        behavioral=behavioral_output(star_method=3.0, ownership=3.5, collaboration=3.0, impact=2.5),
        relevance=relevance_output(
            role_alignment=3.5,
            jd_alignment=3.0,
            question_responsiveness=3.0,
            context_usage=2.5,
        ),
        skipped_agents={AgentName.TECHNICAL_EVALUATION: "Not applicable"},
    )

    result = await judge.judge(context, results)
    output = result.output
    assert isinstance(output, JudgeEvaluationOutput)
    assert output.overall_score <= 45
    assert output.weaknesses
    assert output.priority_improvements
    assert output.dimension_scores.technical is None


@pytest.mark.asyncio
async def test_judge_output_contains_required_fields(judge: JudgeAgent) -> None:
    context = sample_context(InterviewType.TECHNICAL)
    results = build_specialist_results()

    result = await judge.judge(context, results)
    output = result.output
    assert isinstance(output, JudgeEvaluationOutput)

    assert 0 <= output.overall_score <= 100
    assert output.dimension_scores.communication is not None
    assert output.dimension_scores.relevance is not None
    assert output.dimension_scores.structure is not None
    assert output.dimension_scores.confidence is not None
    assert output.dimension_scores.conciseness is not None
    assert output.dimension_scores.technical is not None
    assert output.dimension_scores.problem_solving is not None
    assert output.strongest_dimensions
    assert output.weakest_dimensions
    assert output.weights_applied
    assert output.scoring_methodology_version == "1.1"
