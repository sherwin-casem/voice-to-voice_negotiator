"""Session evaluation results endpoint (status polling + final report)."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session
from app.db.enums import AgentName, EvaluationRunStatus, InterviewSessionStatus
from app.db.models.evaluation import AgentEvaluation, EvaluationRun
from app.modules.auth.deps import get_user_id
from app.modules.evaluation.repository import EvaluationRepository
from app.modules.interview.repository import InterviewRepository
from app.schemas.common import ApiResponse
from app.schemas.evaluation import (
    AgentStatusItem,
    BetterAnswerItem,
    EvaluationDimensionScores,
    EvaluationImprovementItem,
    EvaluationStatusLiteral,
    PracticeRecommendationItem,
    SessionEvaluationData,
    SessionEvaluationResponse,
)

router = APIRouter(tags=["evaluations"])


@router.get(
    "/sessions/{session_id}/evaluation",
    response_model=ApiResponse[SessionEvaluationResponse],
)
async def get_session_evaluation(
    session_id: UUID,
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> ApiResponse[SessionEvaluationResponse]:
    interview_session = await InterviewRepository(db).get_session_for_user(session_id, user_id)
    run = await EvaluationRepository(db).get_latest_session_run_with_details(session_id)
    return ApiResponse(data=_build_response(interview_session.status, session_id, run))


def _build_response(
    session_status: InterviewSessionStatus,
    session_id: UUID,
    run: EvaluationRun | None,
) -> SessionEvaluationResponse:
    return SessionEvaluationResponse(
        session_id=session_id,
        session_status=session_status.value,
        evaluation_status=_evaluation_status(session_status, run),
        evaluation=_build_data(run) if run is not None else None,
        error_message=run.error_message if run is not None else None,
        agents=_agent_statuses(run),
    )


def _evaluation_status(
    session_status: InterviewSessionStatus,
    run: EvaluationRun | None,
) -> EvaluationStatusLiteral:
    if run is not None:
        if run.status == EvaluationRunStatus.COMPLETED:
            return "completed"
        if run.status == EvaluationRunStatus.FAILED:
            return "failed"
        if run.status == EvaluationRunStatus.RUNNING:
            return "running"
        if run.status == EvaluationRunStatus.PENDING:
            return "pending"
        return "unavailable"

    if session_status == InterviewSessionStatus.COMPLETING:
        # Session ended but the background evaluation has not created its run yet.
        return "pending"
    if session_status == InterviewSessionStatus.EVALUATION_FAILED:
        return "failed"
    return "unavailable"


def _agent_statuses(run: EvaluationRun | None) -> list[AgentStatusItem]:
    if run is None:
        return []
    return [
        AgentStatusItem(
            agent_name=agent.agent_name.value,
            status=agent.status.value,
            skipped=agent.skipped,
            summary=agent.summary,
        )
        for agent in run.agent_evaluations
    ]


def _build_data(run: EvaluationRun) -> SessionEvaluationData | None:
    result = run.evaluation_result
    if result is None:
        return None

    judge_output: dict[str, Any] = result.judge_output or {}
    coach_output = _agent_output(run, AgentName.IMPROVEMENT_COACH)

    return SessionEvaluationData(
        overall_score=float(result.overall_score),
        dimension_scores=EvaluationDimensionScores(**(result.dimension_scores or {})),
        strengths=[str(item) for item in result.key_strengths or []],
        weaknesses=[str(item) for item in result.key_gaps or []],
        priority_improvements=_improvements(judge_output),
        better_answers=_better_answers(coach_output),
        practice_recommendations=_practice_recommendations(coach_output),
        did_well=[str(item) for item in (coach_output.get("did_well") or [])],
        should_improve=[str(item) for item in (coach_output.get("should_improve") or [])],
        judge_summary=judge_output.get("summary"),
        coach_summary=coach_output.get("summary"),
        hire_recommendation=(
            result.hire_recommendation.value if result.hire_recommendation else None
        ),
        weights_applied=result.weights_applied or {},
    )


def _agent_output(run: EvaluationRun, agent_name: AgentName) -> dict[str, Any]:
    agent = _find_agent(run, agent_name)
    if agent is None or agent.status != EvaluationRunStatus.COMPLETED:
        return {}
    return agent.output or {}


def _find_agent(run: EvaluationRun, agent_name: AgentName) -> AgentEvaluation | None:
    for agent in run.agent_evaluations:
        if agent.agent_name == agent_name:
            return agent
    return None


def _improvements(judge_output: dict[str, Any]) -> list[EvaluationImprovementItem]:
    items: list[EvaluationImprovementItem] = []
    for raw in judge_output.get("priority_improvements") or []:
        try:
            items.append(
                EvaluationImprovementItem(
                    area=str(raw["area"]),
                    priority=int(raw["priority"]),
                    recommendation=str(raw["recommendation"]),
                    rationale=str(raw["rationale"]) if raw.get("rationale") else None,
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    items.sort(key=lambda item: item.priority)
    return items


def _better_answers(coach_output: dict[str, Any]) -> list[BetterAnswerItem]:
    example = coach_output.get("better_example_answer")
    if not example:
        return []
    return [BetterAnswerItem(question=None, example=str(example))]


def _practice_recommendations(
    coach_output: dict[str, Any],
) -> list[PracticeRecommendationItem]:
    exercise = coach_output.get("practice_exercise")
    if not isinstance(exercise, dict):
        return []
    try:
        return [
            PracticeRecommendationItem(
                title=str(exercise["title"]),
                instructions=str(exercise["instructions"]),
                success_criteria=str(exercise["success_criteria"]),
            )
        ]
    except KeyError:
        return []
