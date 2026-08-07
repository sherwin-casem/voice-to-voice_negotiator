from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

EvaluationStatusLiteral = Literal["pending", "running", "completed", "failed", "unavailable"]


class EvaluationDimensionScores(BaseModel):
    communication: float | None = None
    technical: float | None = None
    relevance: float | None = None
    structure: float | None = None
    confidence: float | None = None
    conciseness: float | None = None
    problem_solving: float | None = None


class EvaluationImprovementItem(BaseModel):
    area: str
    priority: int = Field(ge=1, le=5)
    recommendation: str
    rationale: str | None = None


class PracticeRecommendationItem(BaseModel):
    title: str
    instructions: str
    success_criteria: str


class BetterAnswerItem(BaseModel):
    question: str | None = None
    example: str


class AgentStatusItem(BaseModel):
    agent_name: str
    status: str
    skipped: bool = False
    summary: str | None = None


class SessionEvaluationData(BaseModel):
    overall_score: float
    dimension_scores: EvaluationDimensionScores
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    priority_improvements: list[EvaluationImprovementItem] = Field(default_factory=list)
    better_answers: list[BetterAnswerItem] = Field(default_factory=list)
    practice_recommendations: list[PracticeRecommendationItem] = Field(default_factory=list)
    did_well: list[str] = Field(default_factory=list)
    should_improve: list[str] = Field(default_factory=list)
    judge_summary: str | None = None
    coach_summary: str | None = None
    hire_recommendation: str | None = None
    weights_applied: dict[str, Any] = Field(default_factory=dict)


class SessionEvaluationResponse(BaseModel):
    session_id: UUID
    session_status: str
    evaluation_status: EvaluationStatusLiteral
    evaluation: SessionEvaluationData | None = None
    error_message: str | None = None
    agents: list[AgentStatusItem] = Field(default_factory=list)
