from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.ai.schemas.evaluation.judge import JudgeDimensionScores, JudgeEvaluationOutput
from app.db.enums import AgentName, EvaluationRunStatus, EvaluationScope, InterviewType
from app.modules.evaluation.schemas import AgentExecutionResult, EvaluationRunResult
from app.modules.progress.constants import WeaknessPattern
from app.modules.progress.normalizer import normalize_dimension_score
from app.modules.progress.patterns import detect_recurring_weaknesses
from app.modules.progress.schemas import AnswerMetrics, SessionProgressRecord, TrendDirection
from app.modules.progress.service import ProgressAnalysisService
from app.modules.progress.signals import extract_session_pattern_signals
from tests.evaluation.helpers import build_specialist_results, technical_output


def _record(
    *,
    overall: float,
    technical: float | None = 74.0,
    conciseness: float = 70.0,
    difficulty: str = "mid",
    interview_type: InterviewType = InterviewType.TECHNICAL,
    patterns: tuple[WeaknessPattern, ...] = (),
    offset_days: int = 0,
) -> SessionProgressRecord:
    return SessionProgressRecord(
        session_id=uuid4(),
        user_id=uuid4(),
        interview_type=interview_type,
        difficulty=difficulty,
        recorded_at=datetime.now(UTC) + timedelta(days=offset_days),
        overall_score=overall,
        dimension_scores={
            "communication": overall - 2,
            "technical": technical,
            "relevance": overall - 1,
            "structure": overall - 3,
            "conciseness": conciseness,
            "confidence": overall - 1,
            "problem_solving": technical,
        },
        pattern_signals=patterns,
    )


def test_extract_long_answer_and_filler_signals() -> None:
    long_answer = "um " + "word " * 260 + "you know sort of basically"
    signals = extract_session_pattern_signals(
        answer_metrics=[AnswerMetrics(answer_text=long_answer, word_count=260)],
        specialist_results=[],
        interview_type=InterviewType.BEHAVIORAL,
    )
    assert WeaknessPattern.LONG_ANSWERS in signals
    assert WeaknessPattern.FILLER_WORDS in signals


def test_extract_trade_off_signal_from_technical_evaluator() -> None:
    specialists = build_specialist_results(
        technical=technical_output(trade_off_awareness=4.5),
    )
    signals = extract_session_pattern_signals(
        answer_metrics=[AnswerMetrics(answer_text="I would add caching.", word_count=20)],
        specialist_results=specialists,
        interview_type=InterviewType.TECHNICAL,
    )
    assert WeaknessPattern.WEAK_TRADE_OFF_DISCUSSION in signals


def test_normalizer_applies_difficulty_offset() -> None:
    senior = _record(overall=78, difficulty="senior")
    junior = _record(overall=78, difficulty="junior")
    assert normalize_dimension_score(senior, "overall") == 74.0
    assert normalize_dimension_score(junior, "overall") == 82.0


def test_technical_dimension_not_applicable_for_behavioral_sessions() -> None:
    record = _record(overall=80, interview_type=InterviewType.BEHAVIORAL, technical=None)
    assert normalize_dimension_score(record, "technical") is None


def test_detect_recurring_weaknesses_flags_persistent_patterns() -> None:
    records = [
        _record(overall=70, patterns=(WeaknessPattern.LONG_ANSWERS,)),
        _record(overall=72, patterns=(WeaknessPattern.LONG_ANSWERS, WeaknessPattern.WEAK_CONCLUSION)),
        _record(overall=71, patterns=(WeaknessPattern.LONG_ANSWERS,)),
    ]
    recurring = detect_recurring_weaknesses(records)
    long_answers = next(item for item in recurring if item.pattern == WeaknessPattern.LONG_ANSWERS)
    assert long_answers.is_persistent is True
    assert long_answers.occurrences == 3


def test_progress_analysis_detects_improvement_and_persistent_conciseness() -> None:
    service = ProgressAnalysisService()
    records = [
        _record(overall=68, technical=65, conciseness=58, offset_days=1),
        _record(overall=70, technical=67, conciseness=59, offset_days=2),
        _record(overall=72, technical=70, conciseness=60, offset_days=3),
        _record(overall=78, technical=76, conciseness=57, offset_days=4, patterns=(WeaknessPattern.LONG_ANSWERS,)),
        _record(overall=80, technical=79, conciseness=56, offset_days=5, patterns=(WeaknessPattern.LONG_ANSWERS,)),
    ]
    analysis = service.analyze_records(records, window=5)

    technical_trend = next(t for t in analysis.dimension_trends if t.dimension == "technical")
    assert technical_trend.direction == TrendDirection.IMPROVING
    assert "technical knowledge" in analysis.improvements
    assert "overly long answers" in analysis.persistent_weaknesses
    assert "improved" in analysis.narrative_summary.lower()
    assert "persistent weakness" in analysis.narrative_summary.lower()


def test_progress_analysis_narrative_mentions_last_n_sessions() -> None:
    service = ProgressAnalysisService()
    records = [_record(overall=70 + index, offset_days=index) for index in range(5)]
    analysis = service.analyze_records(records, window=5)
    assert "last 5" in analysis.narrative_summary.lower()


def test_build_record_from_evaluation() -> None:
    service = ProgressAnalysisService()
    judge_output = JudgeEvaluationOutput(
        overall_score=76.0,
        dimension_scores=JudgeDimensionScores(
            communication=78,
            technical=74,
            relevance=81,
            structure=70,
            confidence=77,
            conciseness=65,
            problem_solving=72,
        ),
        summary="Solid answer with room to tighten conciseness and trade-off discussion.",
    )
    judge_result = AgentExecutionResult(
        agent_name=AgentName.SCORING_JUDGE,
        status=EvaluationRunStatus.COMPLETED,
        schema_version="1.0",
        output=judge_output,
    )
    evaluation_result = EvaluationRunResult(
        scope=EvaluationScope.ANSWER,
        orchestration_version="1.2",
        agent_results=build_specialist_results(technical=technical_output(trade_off_awareness=4.0)),
        judge_result=judge_result,
        coach_result=None,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    record = service.build_record_from_evaluation(
        session_id=uuid4(),
        user_id=uuid4(),
        interview_type=InterviewType.TECHNICAL,
        difficulty="senior",
        evaluation_result=evaluation_result,
        answer_metrics=[
            AnswerMetrics(
                answer_text="um well I guess I would sort of add caching you know",
                word_count=240,
            )
        ],
    )
    assert record is not None
    assert record.overall_score == 76.0
    assert WeaknessPattern.WEAK_TRADE_OFF_DISCUSSION in record.pattern_signals
