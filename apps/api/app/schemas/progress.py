from uuid import UUID

from pydantic import BaseModel, Field


class DimensionTrendResponse(BaseModel):
    dimension: str
    label: str
    direction: str
    recent_average: float | None
    prior_average: float | None
    delta: float | None
    sessions_compared: int
    comparable_sessions: int


class RecurringWeaknessResponse(BaseModel):
    pattern: str
    label: str
    occurrences: int
    session_count: int
    frequency: float
    is_persistent: bool


class ProgressAnalysisResponse(BaseModel):
    user_id: UUID | None
    sessions_analyzed: int
    window_size: int
    dimension_trends: list[DimensionTrendResponse]
    recurring_weaknesses: list[RecurringWeaknessResponse]
    improvements: list[str] = Field(default_factory=list)
    persistent_weaknesses: list[str] = Field(default_factory=list)
    narrative_summary: str
