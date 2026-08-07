"""Evaluation persistence flow: full mock evaluation run -> repository rows."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.db.enums import AgentName, EvaluationRunStatus, EvaluationScope, InterviewType
from app.db.models.evaluation import (
    AgentEvaluation,
    EvaluationResult,
    EvaluationRun,
    EvaluationScore,
    ImprovementRecommendation,
)
from app.modules.evaluation.factory import build_evaluation_service
from app.modules.evaluation.repository import EvaluationRepository
from app.modules.evaluation.schemas import EvaluationContext


class RecordingSession:
    """Minimal AsyncSession stand-in that records added ORM objects."""

    def __init__(self, run: EvaluationRun) -> None:
        self._run = run
        self.added: list[object] = []
        self.flush = AsyncMock()

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def get(self, model: type, key: object) -> object | None:
        if model is EvaluationRun and key == self._run.id:
            return self._run
        return None

    def added_of(self, model: type) -> list[object]:
        return [obj for obj in self.added if isinstance(obj, model)]


def _session_context() -> EvaluationContext:
    return EvaluationContext(
        interview_type=InterviewType.TECHNICAL,
        difficulty="senior",
        scope=EvaluationScope.SESSION,
        target_role="Staff Engineer",
        question_text="How would you debug elevated API latency?",
        answer_text=(
            "I would inspect metrics, traces, and recent deploys before narrowing to a bottleneck."
        ),
        topic_tag="debugging",
    )


@pytest.mark.asyncio
async def test_persist_run_result_stores_all_rows() -> None:
    service = build_evaluation_service()
    result = await service.evaluate(_session_context())
    assert result.status == EvaluationRunStatus.COMPLETED

    run_id = uuid.uuid4()
    session_id = uuid.uuid4()
    run = EvaluationRun(
        id=run_id,
        session_id=session_id,
        scope=EvaluationScope.SESSION,
        status=EvaluationRunStatus.RUNNING,
        trigger="session_end",
        orchestration_version="test",
        started_at=datetime.now(UTC),
    )
    session = RecordingSession(run)
    repository = EvaluationRepository(session)  # type: ignore[arg-type]

    persisted = await repository.persist_run_result(run_id, session_id, result)

    assert persisted.status == EvaluationRunStatus.COMPLETED
    assert persisted.completed_at is not None

    # One AgentEvaluation row per specialist plus judge and coach.
    agent_rows = session.added_of(AgentEvaluation)
    expected_agent_count = len(result.agent_results) + 2
    assert len(agent_rows) == expected_agent_count
    row_names = {row.agent_name for row in agent_rows}
    assert AgentName.SCORING_JUDGE in row_names
    assert AgentName.IMPROVEMENT_COACH in row_names

    # Judge dimension scores become EvaluationScore rows (None dimensions dropped).
    judge_output = result.judge_result.output  # type: ignore[union-attr]
    non_null_dimensions = {
        key
        for key, value in judge_output.dimension_scores.model_dump().items()
        if value is not None
    }
    score_rows = session.added_of(EvaluationScore)
    assert {row.dimension_key for row in score_rows} == non_null_dimensions
    assert all(row.session_id == session_id for row in score_rows)

    # Exactly one final result row carrying the judge rollup.
    result_rows = session.added_of(EvaluationResult)
    assert len(result_rows) == 1
    assert float(result_rows[0].overall_score) == pytest.approx(
        float(judge_output.overall_score), abs=0.01
    )
    assert result_rows[0].judge_output["overall_score"] == judge_output.overall_score

    # Judge priority improvements and the coach recommendation are persisted.
    recommendation_rows = session.added_of(ImprovementRecommendation)
    assert len(recommendation_rows) == len(judge_output.priority_improvements) + 1
    coach_rows = [row for row in recommendation_rows if row.practice_plan is not None]
    assert len(coach_rows) == 1


@pytest.mark.asyncio
async def test_persist_run_result_raises_for_unknown_run() -> None:
    service = build_evaluation_service()
    result = await service.evaluate(_session_context())

    run = EvaluationRun(
        id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        scope=EvaluationScope.SESSION,
        status=EvaluationRunStatus.RUNNING,
        trigger="session_end",
        orchestration_version="test",
        started_at=datetime.now(UTC),
    )
    session = RecordingSession(run)
    repository = EvaluationRepository(session)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="not found"):
        await repository.persist_run_result(uuid.uuid4(), run.session_id, result)
