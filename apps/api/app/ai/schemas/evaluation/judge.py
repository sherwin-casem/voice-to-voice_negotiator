from typing import Literal

from pydantic import BaseModel, Field


class JudgeDimensionScores(BaseModel):
    """Normalized dimension scores on a 0–100 scale."""

    communication: float = Field(ge=0, le=100)
    technical: float | None = Field(default=None, ge=0, le=100)
    relevance: float = Field(ge=0, le=100)
    structure: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=100)
    conciseness: float = Field(ge=0, le=100)
    problem_solving: float | None = Field(default=None, ge=0, le=100)


class EvidenceItem(BaseModel):
    quote: str = Field(min_length=5, max_length=500)
    dimension: str = Field(min_length=2, max_length=80)
    supports: Literal["strength", "weakness"]


class PriorityImprovement(BaseModel):
    area: str = Field(min_length=2, max_length=80)
    priority: int = Field(ge=1, le=5)
    recommendation: str = Field(min_length=10, max_length=500)
    rationale: str = Field(min_length=10, max_length=500)


class JudgeEvaluationOutput(BaseModel):
    """Final structured evaluation produced by the Scoring Judge agent."""

    overall_score: float = Field(ge=0, le=100)
    dimension_scores: JudgeDimensionScores
    strengths: list[str] = Field(default_factory=list, max_length=5)
    weaknesses: list[str] = Field(default_factory=list, max_length=5)
    evidence: list[EvidenceItem] = Field(default_factory=list, max_length=8)
    priority_improvements: list[PriorityImprovement] = Field(default_factory=list, max_length=5)
    strongest_dimensions: list[str] = Field(default_factory=list, max_length=3)
    weakest_dimensions: list[str] = Field(default_factory=list, max_length=3)
    conflict_resolutions: list[str] = Field(default_factory=list, max_length=5)
    weights_applied: dict[str, float] = Field(default_factory=dict)
    scoring_methodology_version: str = Field(default="1.0", max_length=20)
    prompt_version: str = Field(default="1.0", max_length=20)
    summary: str = Field(min_length=20, max_length=2000)


class JudgeSynthesisOutput(BaseModel):
    """Qualitative synthesis returned by the LLM judge (numeric scores come from ScoringModel)."""

    strengths: list[str] = Field(default_factory=list, max_length=5)
    weaknesses: list[str] = Field(default_factory=list, max_length=5)
    evidence: list[EvidenceItem] = Field(default_factory=list, max_length=8)
    priority_improvements: list[PriorityImprovement] = Field(default_factory=list, max_length=5)
    summary: str = Field(min_length=20, max_length=2000)
    prompt_version: str = Field(default="1.0", max_length=20)
