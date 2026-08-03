from typing import TypeVar

from pydantic import BaseModel

from app.ai.schemas.evaluation.behavioral import BehavioralDimensions, BehavioralEvaluationOutput
from app.ai.schemas.evaluation.communication import CommunicationDimensions, CommunicationEvaluationOutput
from app.ai.schemas.evaluation.hiring_manager import HiringManagerDimensions, HiringManagerEvaluationOutput
from app.ai.schemas.evaluation.relevance import RelevanceDimensions, RelevanceEvaluationOutput
from app.ai.schemas.evaluation.technical import TechnicalDimensions, TechnicalEvaluationOutput
from app.db.enums import HireRecommendation
from app.modules.evaluation.agents.base import BaseEvaluator, _dimension

T = TypeVar("T", bound=BaseModel)


class MockEvaluationLLMProvider:
    """Deterministic structured outputs for evaluation agent tests."""

    async def generate_structured(
        self,
        messages: list[dict[str, str]] | list,
        response_model: type[T],
        **kwargs: object,
    ) -> T:
        _ = messages, kwargs
        return _build_mock_output(response_model)


def _build_mock_output(response_model: type[T]) -> T:
    if response_model is CommunicationEvaluationOutput:
        return response_model.model_validate(
            {
                "summary": "The candidate communicated clearly with a logical structure and professional tone.",
                "strengths": ["Clear opening", "Professional tone"],
                "gaps": ["Could be more concise"],
                "prompt_version": "1.0",
                "dimensions": CommunicationDimensions(
                    clarity=_dimension(7.5, "Easy to follow explanation."),
                    structure=_dimension(7.0, "Organized answer with clear flow."),
                    conciseness=_dimension(6.0, "Some repetition present."),
                    confidence=_dimension(8.0, "Answered assertively."),
                    tone=_dimension(8.5, "Professional and respectful."),
                ).model_dump(),
            }
        )

    if response_model is TechnicalEvaluationOutput:
        return response_model.model_validate(
            {
                "summary": "The candidate demonstrated solid technical reasoning with reasonable trade-off awareness.",
                "strengths": ["Structured debugging approach"],
                "gaps": ["Limited depth on edge cases"],
                "prompt_version": "1.0",
                "dimensions": TechnicalDimensions(
                    depth=_dimension(7.0, "Covers core concepts."),
                    accuracy=_dimension(7.5, "No major factual issues."),
                    problem_solving=_dimension(7.0, "Logical diagnostic steps."),
                    trade_off_awareness=_dimension(6.5, "Mentions some trade-offs."),
                ).model_dump(),
            }
        )

    if response_model is BehavioralEvaluationOutput:
        return response_model.model_validate(
            {
                "summary": "The candidate used a STAR-style story with clear ownership and team collaboration.",
                "strengths": ["Concrete example", "Clear outcome"],
                "gaps": ["Impact could be quantified further"],
                "prompt_version": "1.0",
                "dimensions": BehavioralDimensions(
                    star_method=_dimension(8.0, "Situation, action, and result are present."),
                    ownership=_dimension(7.5, "Takes personal accountability."),
                    collaboration=_dimension(7.0, "References team coordination."),
                    impact=_dimension(6.5, "Outcome described but not fully quantified."),
                ).model_dump(),
            }
        )

    if response_model is RelevanceEvaluationOutput:
        return response_model.model_validate(
            {
                "summary": "The answer is relevant to the question and aligned with the target role context.",
                "strengths": ["Directly addresses the question"],
                "gaps": ["Could tie more explicitly to JD requirements"],
                "prompt_version": "1.0",
                "dimensions": RelevanceDimensions(
                    role_alignment=_dimension(7.5, "Examples fit the target role."),
                    jd_alignment=_dimension(7.0, "Touches key job requirements."),
                    question_responsiveness=_dimension(8.0, "Stays on topic."),
                    context_usage=_dimension(7.0, "Uses resume context appropriately."),
                ).model_dump(),
            }
        )

    if response_model is HiringManagerEvaluationOutput:
        return response_model.model_validate(
            {
                "summary": "From a hiring manager perspective, the candidate shows promising readiness with manageable risks.",
                "strengths": ["Role-relevant experience"],
                "gaps": ["Needs stronger evidence of senior-level impact"],
                "prompt_version": "1.0",
                "hire_recommendation": HireRecommendation.LEAN_HIRE.value,
                "decision_rationale": "Would proceed to the next round with focus on depth in follow-up questions.",
                "dimensions": HiringManagerDimensions(
                    role_readiness=_dimension(7.0, "Likely able to contribute with onboarding."),
                    culture_fit=_dimension(7.5, "Professional and collaborative signals."),
                    growth_potential=_dimension(7.0, "Shows learning orientation."),
                    risk_assessment=_dimension(6.5, "Some gaps remain in demonstrated depth."),
                ).model_dump(),
            }
        )

    raise TypeError(f"No mock output configured for {response_model.__name__}")
