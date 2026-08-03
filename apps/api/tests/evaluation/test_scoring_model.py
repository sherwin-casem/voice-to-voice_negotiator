from app.db.enums import AgentName, InterviewType
from app.modules.evaluation.judge.scoring_model import ScoringModel
from tests.evaluation.helpers import (
    behavioral_output,
    build_specialist_results,
    communication_output,
    hiring_manager_output,
    relevance_output,
    sample_context,
    technical_output,
)


def test_scoring_model_resolves_communication_relevance_conflict() -> None:
    context = sample_context(InterviewType.TECHNICAL)
    results = build_specialist_results(
        communication=communication_output(clarity=9.5, tone=9.0),
        relevance=relevance_output(question_responsiveness=4.0, role_alignment=5.0),
    )

    baseline = ScoringModel.compute(context, results)

    assert baseline.dimension_scores.communication < 90
    assert baseline.conflict_resolutions
    assert any("responsiveness" in item.lower() for item in baseline.conflict_resolutions)


def test_scoring_model_handles_missing_technical_for_behavioral_interview() -> None:
    context = sample_context(InterviewType.BEHAVIORAL)
    results = build_specialist_results(
        technical=None,
        skipped_agents={AgentName.TECHNICAL_EVALUATION: "Not applicable for behavioral"},
    )

    baseline = ScoringModel.compute(context, results)

    assert baseline.dimension_scores.technical is None
    assert "technical" not in baseline.applicable_dimensions
    assert baseline.overall_score > 0


def test_scoring_model_renormalizes_when_evaluator_failed() -> None:
    context = sample_context(InterviewType.TECHNICAL)
    results = build_specialist_results(failed_agents={AgentName.COMMUNICATION_EVALUATION})

    baseline = ScoringModel.compute(context, results)

    assert baseline.dimension_scores.communication == 50.0
    assert baseline.overall_score > 0
    assert baseline.weights_applied


def test_scoring_model_strong_technical_answer_scores_high() -> None:
    context = sample_context(InterviewType.TECHNICAL)
    results = build_specialist_results(
        communication=communication_output(clarity=9.0, structure=9.0, conciseness=8.5, confidence=9.0, tone=9.0),
        technical=technical_output(depth=9.0, accuracy=9.5, problem_solving=9.0, trade_off_awareness=8.5),
        relevance=relevance_output(
            role_alignment=9.0,
            jd_alignment=8.5,
            question_responsiveness=9.5,
            context_usage=8.5,
        ),
        hiring_manager=hiring_manager_output(role_readiness=8.5, culture_fit=8.0, growth_potential=8.5, risk_assessment=8.0),
    )

    baseline = ScoringModel.compute(context, results)

    assert baseline.overall_score >= 85
    assert baseline.strongest_dimensions


def test_scoring_model_weak_answer_scores_low() -> None:
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

    baseline = ScoringModel.compute(context, results)

    assert baseline.overall_score <= 45
    assert baseline.weakest_dimensions
