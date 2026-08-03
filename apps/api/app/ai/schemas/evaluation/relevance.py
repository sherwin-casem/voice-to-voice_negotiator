from pydantic import BaseModel, Field

from app.ai.schemas.evaluation.common import DimensionScore, SpecialistEvaluationOutput


class RelevanceDimensions(BaseModel):
    role_alignment: DimensionScore
    jd_alignment: DimensionScore
    question_responsiveness: DimensionScore
    context_usage: DimensionScore


class RelevanceEvaluationOutput(SpecialistEvaluationOutput):
    dimensions: RelevanceDimensions
