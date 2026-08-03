import re
from collections.abc import Iterable

from app.ai.schemas.evaluation.behavioral import BehavioralEvaluationOutput
from app.ai.schemas.evaluation.communication import CommunicationEvaluationOutput
from app.ai.schemas.evaluation.technical import TechnicalEvaluationOutput
from app.db.enums import AgentName, InterviewType
from app.modules.evaluation.schemas import AgentExecutionResult
from app.modules.progress.constants import WeaknessPattern
from app.modules.progress.schemas import AnswerMetrics

_FILLER_PATTERN = re.compile(
    r"\b(um+|uh+|erm+|like|you know|sort of|kind of|basically|actually)\b",
    re.IGNORECASE,
)
_CONCRETE_PATTERN = re.compile(
    r"\b(\d+%|\d+\s*(ms|seconds|minutes|hours|days|weeks|months|years|users|requests|dollars|\$|engineers?|people|customers))\b",
    re.IGNORECASE,
)
_OUTCOME_OPENING = re.compile(
    r"^(I (would|will|started|led|built|designed|implemented|reduced|improved|delivered|fixed|migrated|scaled|optimized|achieved|increased|decreased|saved|cut))",
    re.IGNORECASE,
)
_WEAK_OPENING = re.compile(r"^(so|well|okay|yeah|um|uh|I think|I guess|maybe)\b", re.IGNORECASE)
_WEAK_CONCLUSION = re.compile(
    r"(and (that('s| is)? (it|all|everything)|I (think|guess) that('s| is)? it|not sure|don't know)\.?\s*)$",
    re.IGNORECASE,
)

LONG_ANSWER_WORD_THRESHOLD = 220
LOW_STAR_THRESHOLD = 6.0
LOW_TRADE_OFF_THRESHOLD = 6.0
LOW_STRUCTURE_THRESHOLD = 6.0


def extract_session_pattern_signals(
    *,
    answer_metrics: Iterable[AnswerMetrics],
    specialist_results: Iterable[AgentExecutionResult],
    interview_type: InterviewType,
) -> list[WeaknessPattern]:
    signals: set[WeaknessPattern] = set()

    for metrics in answer_metrics:
        signals.update(_signals_from_answer(metrics))

    signals.update(_signals_from_specialists(specialist_results, interview_type))
    return sorted(signals, key=lambda item: item.value)


def _signals_from_answer(metrics: AnswerMetrics) -> set[WeaknessPattern]:
    signals: set[WeaknessPattern] = set()
    text = metrics.answer_text.strip()
    if not text:
        return signals

    word_count = metrics.word_count if metrics.word_count is not None else len(text.split())
    if word_count >= LONG_ANSWER_WORD_THRESHOLD:
        signals.add(WeaknessPattern.LONG_ANSWERS)

    filler_matches = _FILLER_PATTERN.findall(text)
    if len(filler_matches) >= 3:
        signals.add(WeaknessPattern.FILLER_WORDS)

    first_sentence = text.split(".")[0].strip()
    if first_sentence and _WEAK_OPENING.match(first_sentence):
        signals.add(WeaknessPattern.POOR_ANSWER_OPENING)
    elif first_sentence and not _OUTCOME_OPENING.match(first_sentence) and len(first_sentence.split()) > 18:
        signals.add(WeaknessPattern.POOR_ANSWER_OPENING)

    if _WEAK_CONCLUSION.search(text):
        signals.add(WeaknessPattern.WEAK_CONCLUSION)

    if not _CONCRETE_PATTERN.search(text):
        signals.add(WeaknessPattern.LACK_OF_CONCRETE_EXAMPLES)

    return signals


def _signals_from_specialists(
    specialist_results: Iterable[AgentExecutionResult],
    interview_type: InterviewType,
) -> set[WeaknessPattern]:
    signals: set[WeaknessPattern] = set()
    communication = _find_result(specialist_results, AgentName.COMMUNICATION_EVALUATION)
    behavioral = _find_result(specialist_results, AgentName.BEHAVIORAL_EVALUATION)
    technical = _find_result(specialist_results, AgentName.TECHNICAL_EVALUATION)

    if communication and communication.succeeded and isinstance(communication.output, CommunicationEvaluationOutput):
        if communication.output.dimensions.structure.score < LOW_STRUCTURE_THRESHOLD:
            signals.add(WeaknessPattern.POOR_ANSWER_OPENING)

    if behavioral and behavioral.succeeded and isinstance(behavioral.output, BehavioralEvaluationOutput):
        if behavioral.output.dimensions.star_method.score < LOW_STAR_THRESHOLD:
            signals.add(WeaknessPattern.WEAK_STAR_STRUCTURE)

    if (
        interview_type in {InterviewType.TECHNICAL, InterviewType.SYSTEM_DESIGN}
        and technical
        and technical.succeeded
        and isinstance(technical.output, TechnicalEvaluationOutput)
    ):
        if technical.output.dimensions.trade_off_awareness.score < LOW_TRADE_OFF_THRESHOLD:
            signals.add(WeaknessPattern.WEAK_TRADE_OFF_DISCUSSION)

    return signals


def _find_result(
    specialist_results: Iterable[AgentExecutionResult],
    agent_name: AgentName,
) -> AgentExecutionResult | None:
    for result in specialist_results:
        if result.agent_name == agent_name:
            return result
    return None
