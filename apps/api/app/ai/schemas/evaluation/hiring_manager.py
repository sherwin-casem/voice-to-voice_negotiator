from pydantic import BaseModel, Field

from app.ai.schemas.evaluation.common import DimensionScore, SpecialistEvaluationOutput
from app.db.enums import HireRecommendation


class HiringManagerDimensions(BaseModel):
    role_readiness: DimensionScore
    culture_fit: DimensionScore
    growth_potential: DimensionScore
    risk_assessment: DimensionScore


class HiringManagerEvaluationOutput(SpecialistEvaluationOutput):
    dimensions: HiringManagerDimensions
    hire_recommendation: HireRecommendation
    decision_rationale: str = Field(min_length=20, max_length=1500)
