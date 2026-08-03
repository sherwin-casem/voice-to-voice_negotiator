from datetime import UTC, datetime
from uuid import UUID

from app.ai.schemas.evaluation.judge import JudgeEvaluationOutput, JudgeDimensionScores
from app.db.enums import InterviewType
from app.modules.evaluation.schemas import AgentExecutionResult, EvaluationRunResult
from app.modules.progress.constants import DIMENSION_LABELS, WeaknessPattern
from app.modules.progress.normalizer import all_tracked_dimensions, compute_dimension_trend
from app.modules.progress.patterns import detect_recurring_weaknesses
from app.modules.progress.repository import ProgressRepository
from app.modules.progress.schemas import (
    AnswerMetrics,
    DimensionTrend,
    ProgressAnalysis,
    SessionProgressRecord,
    TrendDirection,
)
from app.modules.progress.signals import extract_session_pattern_signals


class ProgressAnalysisService:
    """Summarizes longitudinal interview performance and recurring weaknesses."""

    def __init__(self, repository: ProgressRepository | None = None) -> None:
        self._repository = repository

    async def analyze_user(self, user_id: UUID, *, window: int = 5) -> ProgressAnalysis:
        if self._repository is None:
            return ProgressAnalysis(
                user_id=user_id,
                sessions_analyzed=0,
                window_size=window,
                dimension_trends=[],
                recurring_weaknesses=[],
                narrative_summary="Complete more interview sessions to unlock progress analysis.",
            )
        records = await self._repository.list_snapshots(user_id, limit=max(window * 2, window))
        return self.analyze_records(records, user_id=user_id, window=window)

    async def get_historical_weaknesses(self, user_id: UUID, *, limit: int = 5) -> list[str]:
        analysis = await self.analyze_user(user_id, window=limit)
        weaknesses = list(analysis.persistent_weaknesses)
        for item in analysis.recurring_weaknesses:
            if item.is_persistent and item.label not in weaknesses:
                weaknesses.append(item.label)
        return weaknesses[:limit]

    async def record_session_progress(
        self,
        record: SessionProgressRecord,
        *,
        evaluation_run_id: UUID,
    ) -> None:
        if self._repository is None:
            return
        await self._repository.create_snapshot(record, evaluation_run_id=evaluation_run_id)

    def build_record_from_evaluation(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        interview_type: InterviewType,
        difficulty: str,
        evaluation_result: EvaluationRunResult,
        answer_metrics: list[AnswerMetrics],
        recorded_at: datetime | None = None,
    ) -> SessionProgressRecord | None:
        if not evaluation_result.judge_result or not evaluation_result.judge_result.succeeded:
            return None
        judge_output: JudgeEvaluationOutput = evaluation_result.judge_result.output  # type: ignore[assignment]
        specialist_results = evaluation_result.agent_results
        pattern_signals = extract_session_pattern_signals(
            answer_metrics=answer_metrics,
            specialist_results=specialist_results,
            interview_type=interview_type,
        )
        return SessionProgressRecord(
            session_id=session_id,
            user_id=user_id,
            interview_type=interview_type,
            difficulty=difficulty,
            recorded_at=recorded_at or datetime.now(UTC),
            overall_score=judge_output.overall_score,
            dimension_scores=_dimension_scores_dict(judge_output.dimension_scores),
            pattern_signals=tuple(pattern_signals),
            answer_metrics=tuple(answer_metrics),
        )

    def analyze_records(
        self,
        records: list[SessionProgressRecord],
        *,
        user_id: UUID | None = None,
        window: int = 5,
    ) -> ProgressAnalysis:
        if not records:
            return ProgressAnalysis(
                user_id=user_id,
                sessions_analyzed=0,
                window_size=window,
                dimension_trends=[],
                recurring_weaknesses=[],
                narrative_summary="Complete more interview sessions to unlock progress analysis.",
            )

        recent_records = records[-window:]
        trends = [
            DimensionTrend(
                dimension=dimension,
                direction=direction,
                recent_average=recent_avg,
                prior_average=prior_avg,
                delta=delta,
                sessions_compared=compared,
                comparable_sessions=comparable,
            )
            for dimension in all_tracked_dimensions()
            for direction, recent_avg, prior_avg, delta, compared, comparable in [
                compute_dimension_trend(records, dimension, window=window)
            ]
        ]

        recurring = detect_recurring_weaknesses(recent_records)
        improvements = [
            DIMENSION_LABELS[trend.dimension]
            for trend in trends
            if trend.direction == TrendDirection.IMPROVING and trend.dimension != "overall"
        ]
        persistent = [item.label for item in recurring if item.is_persistent]

        narrative = _build_narrative(
            sessions_analyzed=len(recent_records),
            window=window,
            trends=trends,
            improvements=improvements,
            persistent_weaknesses=persistent,
            recurring=recurring,
        )

        return ProgressAnalysis(
            user_id=user_id,
            sessions_analyzed=len(recent_records),
            window_size=window,
            dimension_trends=trends,
            recurring_weaknesses=recurring,
            improvements=improvements,
            persistent_weaknesses=persistent,
            narrative_summary=narrative,
        )


def _dimension_scores_dict(scores: JudgeDimensionScores) -> dict[str, float | None]:
    return {
        "communication": scores.communication,
        "technical": scores.technical,
        "relevance": scores.relevance,
        "structure": scores.structure,
        "conciseness": scores.conciseness,
        "confidence": scores.confidence,
        "problem_solving": scores.problem_solving,
    }


def _build_narrative(
    *,
    sessions_analyzed: int,
    window: int,
    trends: list[DimensionTrend],
    improvements: list[str],
    persistent_weaknesses: list[str],
    recurring: list,
) -> str:
    if sessions_analyzed == 0:
        return "Complete more interview sessions to unlock progress analysis."

    session_phrase = f"your last {sessions_analyzed} interview{'s' if sessions_analyzed != 1 else ''}"
    if sessions_analyzed < window:
        session_phrase = f"your recent {sessions_analyzed} interview{'s' if sessions_analyzed != 1 else ''}"

    overall_trend = next((t for t in trends if t.dimension == "overall"), None)
    parts: list[str] = []

    if improvements:
        if len(improvements) == 1:
            parts.append(f"You have improved in {improvements[0]} across {session_phrase}.")
        else:
            joined = ", ".join(improvements[:-1]) + f", and {improvements[-1]}"
            parts.append(f"You have improved in {joined} across {session_phrase}.")
    elif overall_trend and overall_trend.direction == TrendDirection.STABLE:
        parts.append(f"Your normalized overall performance has held steady across {session_phrase}.")
    elif overall_trend and overall_trend.direction == TrendDirection.DECLINING:
        parts.append(
            f"Your normalized overall performance has dipped across {session_phrase}; focus on consistency next."
        )

    if persistent_weaknesses:
        primary = persistent_weaknesses[0]
        if len(persistent_weaknesses) == 1:
            parts.append(f"{primary.capitalize()} remains your most persistent weakness across {session_phrase}.")
        else:
            parts.append(
                f"{primary.capitalize()} remains your most persistent weakness across {session_phrase}, "
                f"along with {persistent_weaknesses[1]}."
            )
    elif recurring:
        parts.append(
            f"Across {session_phrase}, watch for recurring {recurring[0].label}; it appeared in "
            f"{recurring[0].occurrences} of {recurring[0].session_count} sessions."
        )
    else:
        parts.append(f"Across {session_phrase}, no single weakness pattern dominates yet.")

    conciseness = next((t for t in trends if t.dimension == "conciseness"), None)
    if (
        conciseness
        and conciseness.direction in {TrendDirection.STABLE, TrendDirection.DECLINING}
        and "conciseness" not in improvements
        and "overly long answers" not in persistent_weaknesses
    ):
        parts.append("Conciseness is not trending up yet compared with your earlier sessions.")

    return " ".join(parts)


def pattern_to_coach_weakness(pattern: WeaknessPattern) -> str:
    mapping = {
        WeaknessPattern.LONG_ANSWERS: "Answers are often longer than needed for the question scope.",
        WeaknessPattern.FILLER_WORDS: "Filler words appear repeatedly under pressure.",
        WeaknessPattern.WEAK_STAR_STRUCTURE: "Behavioral answers often miss clear STAR structure.",
        WeaknessPattern.WEAK_TRADE_OFF_DISCUSSION: "Technical answers under-discuss trade-offs and alternatives.",
        WeaknessPattern.POOR_ANSWER_OPENING: "Answer openings often delay the main point.",
        WeaknessPattern.WEAK_CONCLUSION: "Answers frequently end without a clear takeaway.",
        WeaknessPattern.LACK_OF_CONCRETE_EXAMPLES: "Examples often stay abstract without measurable outcomes.",
    }
    return mapping[pattern]
