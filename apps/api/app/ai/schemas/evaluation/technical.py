from pydantic import BaseModel, Field

from app.ai.schemas.evaluation.common import DimensionScore, SpecialistEvaluationOutput


class TechnicalDimensions(BaseModel):
    depth: DimensionScore
    accuracy: DimensionScore
    problem_solving: DimensionScore
    trade_off_awareness: DimensionScore


class TechnicalEvaluationOutput(SpecialistEvaluationOutput):
    dimensions: TechnicalDimensions
