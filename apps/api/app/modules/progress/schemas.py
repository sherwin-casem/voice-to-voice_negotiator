from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.db.enums import InterviewType
from app.modules.progress.constants import WeaknessPattern


class TrendDirection(StrEnum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class AnswerMetrics:
    answer_text: str
    word_count: int | None = None
    duration_ms: int | None = None
    topic_tag: str | None = None


@dataclass(frozen=True)
class SessionProgressRecord:
    """One completed interview session worth of evaluation data."""

    session_id: UUID
    user_id: UUID
    interview_type: InterviewType
    difficulty: str
    recorded_at: datetime
    overall_score: float
    dimension_scores: dict[str, float | None]
    pattern_signals: tuple[WeaknessPattern, ...] = ()
    answer_metrics: tuple[AnswerMetrics, ...] = ()


@dataclass(frozen=True)
class DimensionTrend:
    dimension: str
    direction: TrendDirection
    recent_average: float | None
    prior_average: float | None
    delta: float | None
    sessions_compared: int
    comparable_sessions: int


@dataclass(frozen=True)
class RecurringWeakness:
    pattern: WeaknessPattern
    label: str
    occurrences: int
    session_count: int
    frequency: float
    is_persistent: bool


@dataclass(frozen=True)
class ProgressAnalysis:
    user_id: UUID | None
    sessions_analyzed: int
    window_size: int
    dimension_trends: list[DimensionTrend]
    recurring_weaknesses: list[RecurringWeakness]
    improvements: list[str] = field(default_factory=list)
    persistent_weaknesses: list[str] = field(default_factory=list)
    narrative_summary: str = ""
