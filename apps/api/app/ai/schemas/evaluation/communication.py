from pydantic import BaseModel, Field

from app.ai.schemas.evaluation.common import DimensionScore, SpecialistEvaluationOutput


class CommunicationDimensions(BaseModel):
    clarity: DimensionScore
    structure: DimensionScore
    conciseness: DimensionScore
    confidence: DimensionScore
    tone: DimensionScore


class CommunicationEvaluationOutput(SpecialistEvaluationOutput):
    dimensions: CommunicationDimensions
