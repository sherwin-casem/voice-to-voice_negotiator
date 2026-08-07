from app.db.enums import InterviewType
from app.modules.progress.constants import TECHNICAL_INTERVIEW_TYPES, TRACKED_DIMENSIONS
from app.modules.progress.schemas import SessionProgressRecord, TrendDirection

DIFFICULTY_OFFSETS: dict[str, float] = {
    "junior": 4.0,
    "mid": 0.0,
    "senior": -4.0,
}


def dimension_applicable(record: SessionProgressRecord, dimension: str) -> bool:
    if dimension == "overall":
        return True
    if dimension == "technical":
        return record.interview_type.value in TECHNICAL_INTERVIEW_TYPES
    # problem_solving is scored for all interview types (behavioral answers are
    # scored on ownership/impact), so it follows the generic presence check.
    return dimension in record.dimension_scores and record.dimension_scores[dimension] is not None


def normalize_dimension_score(
    record: SessionProgressRecord,
    dimension: str,
) -> float | None:
    if dimension == "overall":
        raw = record.overall_score
    else:
        raw = record.dimension_scores.get(dimension)
    if raw is None:
        return None

    difficulty = record.difficulty.lower()
    offset = DIFFICULTY_OFFSETS.get(difficulty, 0.0)
    normalized = raw + offset

    if dimension == "technical" and record.interview_type.value not in TECHNICAL_INTERVIEW_TYPES:
        return None

    return round(max(0.0, min(100.0, normalized)), 1)


def compute_dimension_trend(
    records: list[SessionProgressRecord],
    dimension: str,
    *,
    window: int,
) -> tuple[TrendDirection, float | None, float | None, float | None, int, int]:
    applicable = [record for record in records if dimension_applicable(record, dimension)]
    comparable = len(applicable)
    if comparable < 2:
        return TrendDirection.INSUFFICIENT_DATA, None, None, None, 0, comparable

    if comparable >= 2 * window:
        recent = applicable[-window:]
        prior = applicable[-2 * window : -window]
    else:
        midpoint = max(1, comparable // 2)
        prior = applicable[:midpoint]
        recent = applicable[midpoint:]
        if not recent:
            recent = applicable[-1:]
            prior = applicable[:-1]

    recent_values = [value for record in recent if (value := normalize_dimension_score(record, dimension)) is not None]
    prior_values = [value for record in prior if (value := normalize_dimension_score(record, dimension)) is not None]

    if not recent_values or not prior_values:
        return TrendDirection.INSUFFICIENT_DATA, None, None, None, len(recent_values), comparable

    recent_avg = sum(recent_values) / len(recent_values)
    prior_avg = sum(prior_values) / len(prior_values)
    delta = round(recent_avg - prior_avg, 1)

    if delta >= 3.0:
        direction = TrendDirection.IMPROVING
    elif delta <= -3.0:
        direction = TrendDirection.DECLINING
    else:
        direction = TrendDirection.STABLE

    return direction, round(recent_avg, 1), round(prior_avg, 1), delta, len(recent_values), comparable


def comparable_dimension_records(
    records: list[SessionProgressRecord],
    dimension: str,
) -> list[SessionProgressRecord]:
    return [record for record in records if dimension_applicable(record, dimension)]


def all_tracked_dimensions() -> tuple[str, ...]:
    return TRACKED_DIMENSIONS
