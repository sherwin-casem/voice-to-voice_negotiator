from dataclasses import replace

import pytest

from app.ai.schemas.evaluation.coach import ImprovementCoachOutput, PriorityCoachingFocus, PracticeExercise
from app.ai.schemas.evaluation.judge import (
    EvidenceItem,
    JudgeDimensionScores,
    JudgeEvaluationOutput,
    PriorityImprovement,
)
from app.db.enums import AgentName, InterviewType
from app.modules.evaluation.agents.coach import ImprovementCoachAgent
from app.modules.evaluation.agents.judge import JudgeAgent
from app.modules.evaluation.mock_llm import MockEvaluationLLMProvider
from app.modules.evaluation.schemas import CandidateProfile, CoachInput
from tests.evaluation.helpers import build_specialist_results, sample_context


def _judge_output(
    *,
    overall_score: float = 72.0,
    weakest: list[str] | None = None,
    strongest: list[str] | None = None,
    technical: float | None = 75.0,
    problem_solving: float | None = 70.0,
) -> JudgeEvaluationOutput:
    return JudgeEvaluationOutput(
        overall_score=overall_score,
        dimension_scores=JudgeDimensionScores(
            communication=78.0,
            technical=technical,
            relevance=74.0,
            structure=70.0,
            confidence=76.0,
            conciseness=65.0,
            problem_solving=problem_solving,
        ),
        strengths=["Structured response"],
        weaknesses=["Could be more concise"],
        evidence=[
            EvidenceItem(
                quote="Example quote from the candidate answer.",
                dimension="structure",
                supports="strength",
            )
        ],
        priority_improvements=[
            PriorityImprovement(
                area="conciseness",
                priority=1,
                recommendation="Trim repetition in the middle section.",
                rationale="Conciseness scored lowest.",
            )
        ],
        strongest_dimensions=strongest or ["communication"],
        weakest_dimensions=weakest or ["conciseness"],
        summary="Solid answer with room to tighten delivery.",
    )


def _coach_input(
    interview_type: InterviewType = InterviewType.TECHNICAL,
    *,
    answer_text: str | None = None,
    judge: JudgeEvaluationOutput | None = None,
    historical_weaknesses: list[str] | None = None,
) -> CoachInput:
    base = sample_context(
        interview_type,
        answer_text=answer_text or "I would inspect metrics, traces, and recent deploys before narrowing to a bottleneck.",
    )
    if historical_weaknesses:
        base = replace(base, historical_weaknesses=historical_weaknesses)

    skipped = (
        {AgentName.TECHNICAL_EVALUATION: "Not applicable"}
        if interview_type == InterviewType.BEHAVIORAL
        else {}
    )

    return CoachInput(
        context=base,
        specialist_results=build_specialist_results(skipped_agents=skipped),
        judge_output=judge or _judge_output(),
        historical_weaknesses=historical_weaknesses or [],
    )


@pytest.fixture
def coach() -> ImprovementCoachAgent:
    return ImprovementCoachAgent(MockEvaluationLLMProvider(), model_id="mock-structured")


@pytest.mark.asyncio
async def test_coach_produces_structured_output(coach: ImprovementCoachAgent) -> None:
    result = await coach.coach(_coach_input())

    assert result.succeeded
    output = result.output
    assert isinstance(output, ImprovementCoachOutput)
    assert output.did_well
    assert output.should_improve
    assert output.highest_priority.specific_action
    assert output.practice_exercise.instructions
    assert output.evidence_citations


@pytest.mark.asyncio
async def test_coach_strong_technical_answer(coach: ImprovementCoachAgent) -> None:
    result = await coach.coach(
        _coach_input(
            InterviewType.TECHNICAL,
            answer_text=(
                "The root cause was a downstream timeout. I used APM latency dashboards, "
                "traced failing requests, and deployed circuit breakers to restore p95 latency."
            ),
            judge=_judge_output(overall_score=88.0, weakest=["conciseness"], strongest=["technical"]),
        )
    )

    output = result.output
    assert isinstance(output, ImprovementCoachOutput)
    assert "bur" in output.highest_priority.improvement.lower() or "headline" in output.highest_priority.improvement.lower()
    assert output.better_example_answer


@pytest.mark.asyncio
async def test_coach_weak_behavioral_answer(coach: ImprovementCoachAgent) -> None:
    result = await coach.coach(
        _coach_input(
            InterviewType.BEHAVIORAL,
            answer_text="I guess I would try to handle it somehow.",
            judge=_judge_output(
                overall_score=35.0,
                weakest=["structure"],
                strongest=["relevance"],
                technical=None,
                problem_solving=40.0,
            ),
        )
    )

    output = result.output
    assert isinstance(output, ImprovementCoachOutput)
    assert "guess" in output.highest_priority.improvement.lower() or "specific" in output.highest_priority.improvement.lower()
    assert "STAR" in output.better_example_answer or "team lead" in output.better_example_answer


@pytest.mark.asyncio
async def test_coach_references_historical_weaknesses(coach: ImprovementCoachAgent) -> None:
    result = await coach.coach(
        _coach_input(
            historical_weaknesses=["Answers often lack measurable outcomes"],
        )
    )

    output = result.output
    assert isinstance(output, ImprovementCoachOutput)
    assert any("prior pattern" in item.lower() for item in output.should_improve)


@pytest.mark.asyncio
async def test_coach_feedback_is_specific_not_generic(coach: ImprovementCoachAgent) -> None:
    result = await coach.coach(_coach_input())
    output = result.output
    assert isinstance(output, ImprovementCoachOutput)

    combined = " ".join(output.did_well + output.should_improve + [output.highest_priority.improvement])
    assert "improve your communication" not in combined.lower()
    assert len(output.highest_priority.improvement) >= 30


def test_coach_schema_rejects_generic_feedback() -> None:
    with pytest.raises(ValueError, match="too generic"):
        ImprovementCoachOutput(
            did_well=["Improve your communication"],
            should_improve=["You should be more confident in interviews."],
            highest_priority=PriorityCoachingFocus(
                area="communication",
                improvement="Your answer spends most of its time describing implementation details before explaining the business outcome. Start with the result, then explain the technical decisions that produced it.",
                why_it_matters="Hiring managers need to hear impact quickly for senior roles.",
                specific_action="Record a 90-second retake opening with the outcome in sentence one.",
            ),
            practice_exercise=PracticeExercise(
                title="Outcome-first retake",
                instructions="Rewrite and record the answer with outcome first.",
                success_criteria="First sentence states a measurable result.",
            ),
            summary="Focus on leading with impact before diving into implementation details in your next practice session.",
        )


@pytest.mark.asyncio
async def test_full_pipeline_includes_coach_via_service() -> None:
    from app.modules.evaluation.factory import build_evaluation_service

    service = build_evaluation_service()
    context = sample_context(InterviewType.TECHNICAL)
    result = await service.evaluate(context)

    assert result.coach_result is not None
    assert result.coach_result.succeeded
    assert isinstance(result.coach_result.output, ImprovementCoachOutput)
