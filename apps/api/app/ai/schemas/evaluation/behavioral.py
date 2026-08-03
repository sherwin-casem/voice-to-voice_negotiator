from pydantic import BaseModel, Field

from app.ai.schemas.evaluation.common import DimensionScore, SpecialistEvaluationOutput


class BehavioralDimensions(BaseModel):
    star_method: DimensionScore
    ownership: DimensionScore
    collaboration: DimensionScore
    impact: DimensionScore


class BehavioralEvaluationOutput(SpecialistEvaluationOutput):
    dimensions: BehavioralDimensions
