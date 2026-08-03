from dataclasses import dataclass, field

from app.ai.schemas.evaluation.judge import JudgeDimensionScores
from app.db.enums import AgentName, InterviewType
from app.modules.evaluation.schemas import AgentExecutionResult, EvaluationContext

METHODOLOGY_VERSION = "1.0"

INTERVIEW_WEIGHTS: dict[InterviewType, dict[str, float]] = {
    InterviewType.TECHNICAL: {
        "communication": 0.12,
        "technical": 0.28,
        "relevance": 0.15,
        "structure": 0.10,
        "confidence": 0.10,
        "conciseness": 0.05,
        "problem_solving": 0.20,
    },
    InterviewType.SYSTEM_DESIGN: {
        "communication": 0.12,
        "technical": 0.22,
        "relevance": 0.12,
        "structure": 0.12,
        "confidence": 0.10,
        "conciseness": 0.05,
        "problem_solving": 0.27,
    },
    InterviewType.BEHAVIORAL: {
        "communication": 0.22,
        "relevance": 0.18,
        "structure": 0.18,
        "confidence": 0.15,
        "conciseness": 0.12,
        "problem_solving": 0.15,
    },
    InterviewType.LEADERSHIP: {
        "communication": 0.20,
        "relevance": 0.16,
        "structure": 0.16,
        "confidence": 0.16,
        "conciseness": 0.10,
        "problem_solving": 0.22,
    },
    InterviewType.HR: {
        "communication": 0.24,
        "relevance": 0.22,
        "structure": 0.14,
        "confidence": 0.14,
        "conciseness": 0.12,
        "problem_solving": 0.14,
    },
}


@dataclass(frozen=True)
class ScoringBaseline:
    dimension_scores: JudgeDimensionScores
    overall_score: float
    weights_applied: dict[str, float]
    applicable_dimensions: list[str]
    strongest_dimensions: list[str]
    weakest_dimensions: list[str]
    conflict_resolutions: list[str] = field(default_factory=list)


def _scale(score: float) -> float:
    return round(max(0.0, min(10.0, score)) * 10.0, 1)


def _avg(*values: float) -> float:
    return sum(values) / len(values)


def _get_result(
    results: list[AgentExecutionResult],
    agent_name: AgentName,
) -> AgentExecutionResult | None:
    for result in results:
        if result.agent_name == agent_name:
            return result
    return None


class ScoringModel:
    """Transparent deterministic rollup from specialist outputs to 0–100 scores."""

    @classmethod
    def compute(
        cls,
        context: EvaluationContext,
        specialist_results: list[AgentExecutionResult],
    ) -> ScoringBaseline:
        communication = _get_result(specialist_results, AgentName.COMMUNICATION_EVALUATION)
        technical = _get_result(specialist_results, AgentName.TECHNICAL_EVALUATION)
        behavioral = _get_result(specialist_results, AgentName.BEHAVIORAL_EVALUATION)
        relevance = _get_result(specialist_results, AgentName.RELEVANCE_EVALUATION)
        hiring_manager = _get_result(specialist_results, AgentName.HIRING_MANAGER_EVALUATION)

        conflict_resolutions: list[str] = []

        comm_score = cls._communication_dimension(communication)
        structure_score = cls._structure_dimension(communication, behavioral)
        conciseness_score = cls._conciseness_dimension(communication)
        confidence_score = cls._confidence_dimension(communication)
        relevance_score = cls._relevance_dimension(relevance)
        technical_score = cls._technical_dimension(technical, context.interview_type)
        problem_solving_score = cls._problem_solving_dimension(
            technical,
            behavioral,
            context.interview_type,
        )

        if communication and relevance and communication.succeeded and relevance.succeeded:
            comm_out = communication.output
            rel_out = relevance.output
            clarity = _scale(comm_out.dimensions.clarity.score)  # type: ignore[union-attr]
            responsiveness = _scale(rel_out.dimensions.question_responsiveness.score)  # type: ignore[union-attr]
            if clarity - responsiveness >= 25:
                adjusted = round((clarity * 0.4) + (responsiveness * 0.6), 1)
                conflict_resolutions.append(
                    "Communication clarity exceeded question responsiveness; "
                    f"communication score adjusted from {comm_score} to {adjusted} "
                    "to reflect relevance conflict."
                )
                comm_score = adjusted

        if technical and hiring_manager and technical.succeeded and hiring_manager.succeeded:
            tech_out = technical.output
            hm_out = hiring_manager.output
            tech_readiness = _scale(
                _avg(tech_out.dimensions.depth.score, tech_out.dimensions.accuracy.score)  # type: ignore[union-attr]
            )
            hm_readiness = _scale(hm_out.dimensions.role_readiness.score)  # type: ignore[union-attr]
            if abs(tech_readiness - hm_readiness) > 25:
                if context.interview_type in {InterviewType.TECHNICAL, InterviewType.SYSTEM_DESIGN}:
                    blended = round((tech_readiness * 0.7) + (hm_readiness * 0.3), 1)
                    conflict_resolutions.append(
                        "Technical depth and hiring-manager readiness diverged; "
                        f"technical score set to {blended} using 70/30 technical/hiring-manager weighting."
                    )
                    technical_score = blended
                else:
                    blended = round((tech_readiness * 0.35) + (hm_readiness * 0.65), 1)
                    if technical_score is not None:
                        conflict_resolutions.append(
                            "Hiring-manager readiness diverged from technical signals; "
                            f"technical score adjusted to {blended}."
                        )
                        technical_score = blended

        dimension_scores = JudgeDimensionScores(
            communication=comm_score,
            technical=technical_score,
            relevance=relevance_score,
            structure=structure_score,
            confidence=confidence_score,
            conciseness=conciseness_score,
            problem_solving=problem_solving_score,
        )

        weights = dict(INTERVIEW_WEIGHTS[context.interview_type])
        applicable, weights_applied, overall = cls._weighted_overall(dimension_scores, weights)
        strongest, weakest = cls._rank_dimensions(dimension_scores, applicable)

        return ScoringBaseline(
            dimension_scores=dimension_scores,
            overall_score=overall,
            weights_applied=weights_applied,
            applicable_dimensions=applicable,
            strongest_dimensions=strongest,
            weakest_dimensions=weakest,
            conflict_resolutions=conflict_resolutions,
        )

    @staticmethod
    def _communication_dimension(result: AgentExecutionResult | None) -> float:
        if result is None or not result.succeeded or result.output is None:
            return 50.0
        dims = result.output.dimensions  # type: ignore[attr-defined]
        return round(_avg(_scale(dims.clarity.score), _scale(dims.tone.score)), 1)

    @staticmethod
    def _structure_dimension(
        communication: AgentExecutionResult | None,
        behavioral: AgentExecutionResult | None,
    ) -> float:
        scores: list[float] = []
        if communication and communication.succeeded and communication.output is not None:
            scores.append(_scale(communication.output.dimensions.structure.score))  # type: ignore[union-attr]
        if behavioral and behavioral.succeeded and behavioral.output is not None:
            scores.append(_scale(behavioral.output.dimensions.star_method.score))  # type: ignore[union-attr]
        if not scores:
            return 50.0
        if len(scores) == 2:
            return round((scores[0] * 0.65) + (scores[1] * 0.35), 1)
        return scores[0]

    @staticmethod
    def _conciseness_dimension(result: AgentExecutionResult | None) -> float:
        if result is None or not result.succeeded or result.output is None:
            return 50.0
        return _scale(result.output.dimensions.conciseness.score)  # type: ignore[union-attr]

    @staticmethod
    def _confidence_dimension(result: AgentExecutionResult | None) -> float:
        if result is None or not result.succeeded or result.output is None:
            return 50.0
        return _scale(result.output.dimensions.confidence.score)  # type: ignore[union-attr]

    @staticmethod
    def _relevance_dimension(result: AgentExecutionResult | None) -> float:
        if result is None or not result.succeeded or result.output is None:
            return 50.0
        dims = result.output.dimensions  # type: ignore[attr-defined]
        return round(
            _avg(
                _scale(dims.role_alignment.score),
                _scale(dims.jd_alignment.score),
                _scale(dims.question_responsiveness.score),
                _scale(dims.context_usage.score),
            ),
            1,
        )

    @staticmethod
    def _technical_dimension(
        result: AgentExecutionResult | None,
        interview_type: InterviewType,
    ) -> float | None:
        if interview_type in {
            InterviewType.BEHAVIORAL,
            InterviewType.HR,
            InterviewType.LEADERSHIP,
        }:
            return None
        if result is None or result.skipped or not result.succeeded or result.output is None:
            return None
        dims = result.output.dimensions  # type: ignore[attr-defined]
        return round(_avg(_scale(dims.depth.score), _scale(dims.accuracy.score)), 1)

    @staticmethod
    def _problem_solving_dimension(
        technical: AgentExecutionResult | None,
        behavioral: AgentExecutionResult | None,
        interview_type: InterviewType,
    ) -> float | None:
        if interview_type in {InterviewType.TECHNICAL, InterviewType.SYSTEM_DESIGN}:
            if technical and technical.succeeded and technical.output is not None:
                dims = technical.output.dimensions  # type: ignore[attr-defined]
                return round(
                    _avg(
                        _scale(dims.problem_solving.score),
                        _scale(dims.trade_off_awareness.score),
                    ),
                    1,
                )
            return None

        if behavioral and behavioral.succeeded and behavioral.output is not None:
            dims = behavioral.output.dimensions  # type: ignore[attr-defined]
            return round(
                _avg(_scale(dims.star_method.score), _scale(dims.impact.score)),
                1,
            )
        return None

    @staticmethod
    def _weighted_overall(
        scores: JudgeDimensionScores,
        weights: dict[str, float],
    ) -> tuple[list[str], dict[str, float], float]:
        values = {
            "communication": scores.communication,
            "technical": scores.technical,
            "relevance": scores.relevance,
            "structure": scores.structure,
            "confidence": scores.confidence,
            "conciseness": scores.conciseness,
            "problem_solving": scores.problem_solving,
        }

        applicable = [key for key, value in values.items() if value is not None and weights.get(key, 0) > 0]
        if not applicable:
            applicable = [key for key, value in values.items() if value is not None]
        if not applicable:
            return [], {}, 0.0

        active_weight_sum = sum(weights.get(key, 0.0) for key in applicable)
        if active_weight_sum <= 0:
            normalized = {key: 1.0 / len(applicable) for key in applicable}
        else:
            normalized = {key: weights.get(key, 0.0) / active_weight_sum for key in applicable}

        overall = round(
            sum(values[key] * normalized[key] for key in applicable),  # type: ignore[index, operator]
            1,
        )
        return applicable, normalized, overall

    @staticmethod
    def _rank_dimensions(
        scores: JudgeDimensionScores,
        applicable: list[str],
    ) -> tuple[list[str], list[str]]:
        values = {
            "communication": scores.communication,
            "technical": scores.technical,
            "relevance": scores.relevance,
            "structure": scores.structure,
            "confidence": scores.confidence,
            "conciseness": scores.conciseness,
            "problem_solving": scores.problem_solving,
        }
        ranked = sorted(
            ((name, values[name]) for name in applicable if values[name] is not None),
            key=lambda item: item[1],
            reverse=True,
        )
        if not ranked:
            return [], []
        strongest = [name for name, _ in ranked[:2]]
        weakest = [name for name, _ in ranked[-2:]]
        return strongest, weakest
