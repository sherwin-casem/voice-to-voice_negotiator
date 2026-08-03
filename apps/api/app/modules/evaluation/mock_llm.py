from typing import TypeVar

from pydantic import BaseModel

from app.ai.schemas.evaluation.behavioral import BehavioralDimensions, BehavioralEvaluationOutput
from app.ai.schemas.evaluation.communication import CommunicationDimensions, CommunicationEvaluationOutput
from app.ai.schemas.evaluation.hiring_manager import HiringManagerDimensions, HiringManagerEvaluationOutput
from app.ai.schemas.evaluation.coach import (
    ImprovementCoachOutput,
    PracticeExercise,
    PriorityCoachingFocus,
)
from app.ai.schemas.evaluation.judge import EvidenceItem, JudgeSynthesisOutput, PriorityImprovement
from app.ai.schemas.evaluation.relevance import RelevanceDimensions, RelevanceEvaluationOutput
from app.ai.schemas.evaluation.technical import TechnicalDimensions, TechnicalEvaluationOutput
from app.db.enums import HireRecommendation
from app.modules.evaluation.agents.base import BaseEvaluator, _dimension
from app.modules.evaluation.judge.scoring_model import ScoringBaseline
from app.modules.evaluation.schemas import CoachInput

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


def build_mock_judge_synthesis(context, baseline: ScoringBaseline) -> JudgeSynthesisOutput:
    excerpt = context.answer_text[:100].strip()
    if len(context.answer_text) > 100:
        excerpt += "..."

    if baseline.overall_score >= 75:
        strengths = [
            "Clear and structured response",
            f"Strong performance in {', '.join(baseline.strongest_dimensions)}",
        ]
        weaknesses = [f"Room to improve {baseline.weakest_dimensions[0]}"]
        supports: str = "strength"
    elif baseline.overall_score <= 45:
        strengths = ["Provides a response to the question"]
        weaknesses = [
            "Limited depth and specificity",
            f"Weak {', '.join(baseline.weakest_dimensions)}",
        ]
        supports = "weakness"
    else:
        strengths = [f"Adequate {baseline.strongest_dimensions[0]}"]
        weaknesses = [f"Needs improvement in {baseline.weakest_dimensions[0]}"]
        supports = "strength" if baseline.overall_score >= 60 else "weakness"

    weakest = baseline.weakest_dimensions[0] if baseline.weakest_dimensions else "communication"

    return JudgeSynthesisOutput(
        strengths=strengths,
        weaknesses=weaknesses,
        evidence=[
            EvidenceItem(
                quote=excerpt or context.answer_text,
                dimension=weakest,
                supports=supports,  # type: ignore[arg-type]
            )
        ],
        priority_improvements=[
            PriorityImprovement(
                area=weakest,
                priority=1,
                recommendation=f"Practice improving {weakest} with targeted mock answers.",
                rationale=f"Scoring model identified {weakest} as a priority gap.",
            )
        ],
        summary=(
            f"Overall score {baseline.overall_score}/100. "
            f"Strongest dimensions: {', '.join(baseline.strongest_dimensions) or 'n/a'}. "
            f"Weakest dimensions: {', '.join(baseline.weakest_dimensions) or 'n/a'}."
        ),
        prompt_version="1.0",
    )


def build_mock_coach_output(coach_input: CoachInput) -> ImprovementCoachOutput:
    context = coach_input.context
    judge = coach_input.judge_output
    excerpt = context.answer_text[:90].strip()
    if len(context.answer_text) > 90:
        excerpt += "..."

    weakest = judge.weakest_dimensions[0] if judge.weakest_dimensions else "structure"
    strongest = judge.strongest_dimensions[0] if judge.strongest_dimensions else "relevance"
    historical = coach_input.historical_weaknesses or context.historical_weaknesses

    if judge.overall_score >= 75:
        did_well = [
            f"You directly addressed the question and showed strength in {strongest}, "
            f"especially where you stated: \"{excerpt}\"",
        ]
        should_improve = [
            f"To reach the next level, tighten the {weakest} dimension by ending with a clearer takeaway "
            "before adding supporting detail.",
        ]
        priority_improvement = (
            "Your answer is strong but buries the headline. Lead with the main conclusion in one sentence, "
            "then support it with the details you already included."
        )
        example = (
            "Start with: 'The root cause was a downstream dependency timeout, which we fixed by adding circuit "
            "breakers and cache warming.' Then walk through metrics, traces, and deploy checks."
        )
    elif judge.overall_score <= 45:
        did_well = [
            "You attempted to respond to the question rather than skipping it, which gives a baseline to refine.",
        ]
        should_improve = [
            "The answer stays abstract and does not walk through a concrete situation, action, and outcome "
            f"with specific details from your experience.",
        ]
        if context.interview_type.value in {"behavioral", "leadership", "hr"}:
            priority_improvement = (
                "Your answer opens with vague intent ('I guess I would...') instead of a specific example. "
                "Replace that opener with one sentence naming the situation and your role before describing actions."
            )
            example = (
                "Instead of 'I guess I would try to handle it somehow,' try: 'In my last role as team lead, "
                "two engineers disagreed on an API contract. I scheduled a 30-minute design review, documented "
                "decision criteria, and we shipped a compromise within a week.'"
            )
        else:
            priority_improvement = (
                "Your answer lists intentions but not a diagnostic sequence tied to the question. "
                "Name the first signal you would inspect, the tool or metric you would check, and the decision "
                "that narrows the bottleneck."
            )
            example = (
                "Open with: 'I would start with p95 latency by endpoint in our APM, compare against the last "
                "deploy, then trace the slowest requests to isolate the dependency.'"
            )
    else:
        did_well = [
            f"You covered relevant content for a {context.interview_type.value} interview, "
            f"with relative strength in {strongest}.",
        ]
        should_improve = [
            f"The answer would land more clearly with stronger {weakest}, particularly in how you order "
            "context, actions, and results.",
        ]
        priority_improvement = (
            f"Re-order your response so the listener hears the outcome before implementation details. "
            f"In your current answer, the opening focuses on process before impact, which weakens {weakest}."
        )
        example = (
            "Lead with the result or recommendation first, then explain the 2–3 key steps that produced it."
        )

    if historical:
        should_improve.append(
            f"This repeats a prior pattern ({historical[0]}). Apply the same structural fix in this answer type."
        )

    return ImprovementCoachOutput(
        did_well=did_well,
        should_improve=should_improve,
        highest_priority=PriorityCoachingFocus(
            area=weakest,
            improvement=priority_improvement,
            why_it_matters=(
                f"Interviewers weight {weakest} heavily for {context.target_role or 'this role'} at "
                f"{context.difficulty} level because it signals readiness to communicate impact clearly."
            ),
            specific_action=(
                "Record a 90-second retake: first sentence = outcome, next two sentences = key actions, "
                "final sentence = measurable result or trade-off."
            ),
        ),
        better_example_answer=example,
        practice_exercise=PracticeExercise(
            title=f"{weakest.title()} retake drill",
            instructions=(
                "Pick the same question, write a bullet outline with Outcome → Actions → Result, "
                "then record a 90-second spoken answer without reading verbatim."
            ),
            success_criteria=(
                "The first sentence states the outcome; the answer includes at least one concrete metric "
                "or decision; no vague openers such as 'I guess' or 'I would try to.'"
            ),
        ),
        evidence_citations=[excerpt or context.answer_text[:120]],
        prompt_version="1.0",
        summary=(
            f"Focus on {weakest} in your next practice pass. Your score was {judge.overall_score}/100; "
            "the retake drill above targets the highest-impact fix."
        ),
    )
