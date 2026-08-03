from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    """Score for a single rubric dimension on a 0–10 scale."""

    score: float = Field(ge=0, le=10)
    max_score: float = Field(default=10.0, ge=1, le=10)
    evidence: list[str] = Field(default_factory=list, max_length=5)
    rationale: str = Field(min_length=1, max_length=500)


class SpecialistEvaluationOutput(BaseModel):
    """Shared fields returned by all specialist evaluation agents."""

    summary: str = Field(min_length=20, max_length=2000)
    strengths: list[str] = Field(default_factory=list, max_length=5)
    gaps: list[str] = Field(default_factory=list, max_length=5)
    prompt_version: str = Field(default="1.0", max_length=20)
