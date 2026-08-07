"""Persistence for multi-agent evaluation runs and their results."""

import logging
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.enums import AgentName, EvaluationRunStatus, EvaluationScope, HireRecommendation
from app.db.models.evaluation import (
    AgentEvaluation,
    EvaluationResult,
    EvaluationRun,
    EvaluationScore,
    ImprovementRecommendation,
)
from app.modules.evaluation.schemas import AgentExecutionResult, EvaluationRunResult

logger = logging.getLogger(__name__)


class EvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_session_run(self, session_id: UUID) -> EvaluationRun | None:
        result = await self._session.execute(
            select(EvaluationRun)
            .where(
                EvaluationRun.session_id == session_id,
                EvaluationRun.scope == EvaluationScope.SESSION,
            )
            .order_by(EvaluationRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_session_run_with_details(
        self,
        session_id: UUID,
    ) -> EvaluationRun | None:
        result = await self._session.execute(
            select(EvaluationRun)
            .where(
                EvaluationRun.session_id == session_id,
                EvaluationRun.scope == EvaluationScope.SESSION,
            )
            .options(
                selectinload(EvaluationRun.agent_evaluations),
                selectinload(EvaluationRun.evaluation_result),
                selectinload(EvaluationRun.improvement_recommendations),
            )
            .order_by(EvaluationRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_run(
        self,
        session_id: UUID,
        *,
        scope: EvaluationScope,
        trigger: str,
        orchestration_version: str,
        answer_id: UUID | None = None,
    ) -> EvaluationRun:
        run = EvaluationRun(
            session_id=session_id,
            answer_id=answer_id,
            scope=scope,
            status=EvaluationRunStatus.RUNNING,
            trigger=trigger,
            orchestration_version=orchestration_version,
            started_at=datetime.now(UTC),
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def mark_run_failed(self, run_id: UUID, error_message: str) -> None:
        run = await self._session.get(EvaluationRun, run_id)
        if run is None:
            return
        run.status = EvaluationRunStatus.FAILED
        run.error_message = error_message[:2000]
        run.completed_at = datetime.now(UTC)
        await self._session.flush()

    async def persist_run_result(
        self,
        run_id: UUID,
        session_id: UUID,
        result: EvaluationRunResult,
        *,
        answer_id: UUID | None = None,
    ) -> EvaluationRun:
        run = await self._session.get(EvaluationRun, run_id)
        if run is None:
            raise ValueError(f"Evaluation run {run_id} not found")

        run.status = result.status
        run.started_at = result.started_at
        run.completed_at = result.completed_at
        if result.judge_result is not None and result.judge_result.error_message:
            run.error_message = result.judge_result.error_message[:2000]

        all_agent_results = list(result.agent_results)
        if result.judge_result is not None:
            all_agent_results.append(result.judge_result)
        if result.coach_result is not None:
            all_agent_results.append(result.coach_result)

        agent_rows: dict[AgentName, AgentEvaluation] = {}
        for agent_result in all_agent_results:
            row = self._to_agent_evaluation(run_id, agent_result)
            self._session.add(row)
            agent_rows[agent_result.agent_name] = row
        await self._session.flush()

        judge = result.judge_result
        if judge is not None and judge.succeeded and judge.output is not None:
            judge_row = agent_rows[judge.agent_name]
            self._persist_judge_scores(run, judge_row, judge, session_id, answer_id)
            self._persist_result_row(run, judge, result, session_id, answer_id)
            self._persist_judge_recommendations(run, judge_row, judge, session_id, answer_id)

        coach = result.coach_result
        if coach is not None and coach.succeeded and coach.output is not None:
            coach_row = agent_rows[coach.agent_name]
            self._persist_coach_recommendation(run, coach_row, coach, session_id, answer_id)

        await self._session.flush()
        return run

    @staticmethod
    def _to_agent_evaluation(
        run_id: UUID,
        agent_result: AgentExecutionResult,
    ) -> AgentEvaluation:
        output_payload: dict[str, Any] = {}
        summary: str | None = None
        if agent_result.output is not None:
            output_payload = agent_result.output.model_dump(mode="json")
            raw_summary = output_payload.get("summary")
            summary = str(raw_summary) if raw_summary else None

        token_usage = None
        if agent_result.token_usage is not None:
            token_usage = asdict(agent_result.token_usage)

        return AgentEvaluation(
            evaluation_run_id=run_id,
            agent_name=agent_result.agent_name,
            schema_version=agent_result.schema_version,
            status=agent_result.status,
            skipped=agent_result.skipped,
            skip_reason=agent_result.skip_reason,
            model_id=agent_result.model_id,
            prompt_version=agent_result.prompt_version,
            summary=summary,
            output=output_payload,
            latency_ms=agent_result.latency_ms,
            token_usage=token_usage,
            started_at=agent_result.started_at,
            completed_at=agent_result.completed_at,
        )

    def _persist_judge_scores(
        self,
        run: EvaluationRun,
        judge_row: AgentEvaluation,
        judge: AgentExecutionResult,
        session_id: UUID,
        answer_id: UUID | None,
    ) -> None:
        output = judge.output
        assert output is not None
        dimension_scores = output.dimension_scores.model_dump()
        weights = output.weights_applied or {}
        evidence_by_dimension: dict[str, list[dict[str, str]]] = {}
        for item in output.evidence:
            evidence_by_dimension.setdefault(item.dimension, []).append(
                {"quote": item.quote, "supports": item.supports}
            )

        for dimension_key, score in dimension_scores.items():
            if score is None:
                continue
            self._session.add(
                EvaluationScore(
                    agent_evaluation_id=judge_row.id,
                    evaluation_run_id=run.id,
                    session_id=session_id,
                    answer_id=answer_id,
                    agent_name=judge.agent_name,
                    dimension_key=dimension_key,
                    score=Decimal(str(round(float(score), 2))),
                    max_score=Decimal("100"),
                    weight=(
                        Decimal(str(round(float(weights[dimension_key]), 4)))
                        if dimension_key in weights
                        else None
                    ),
                    evidence=evidence_by_dimension.get(dimension_key, []),
                )
            )

    def _persist_result_row(
        self,
        run: EvaluationRun,
        judge: AgentExecutionResult,
        result: EvaluationRunResult,
        session_id: UUID,
        answer_id: UUID | None,
    ) -> None:
        output = judge.output
        assert output is not None
        self._session.add(
            EvaluationResult(
                evaluation_run_id=run.id,
                session_id=session_id,
                answer_id=answer_id,
                overall_score=Decimal(str(round(float(output.overall_score), 2))),
                overall_max=Decimal("100"),
                hire_recommendation=self._extract_hire_recommendation(result),
                dimension_scores=output.dimension_scores.model_dump(mode="json"),
                weights_applied=output.weights_applied,
                key_strengths=list(output.strengths),
                key_gaps=list(output.weaknesses),
                judge_output=output.model_dump(mode="json"),
            )
        )

    @staticmethod
    def _extract_hire_recommendation(result: EvaluationRunResult) -> HireRecommendation | None:
        for agent_result in result.agent_results:
            if agent_result.agent_name != AgentName.HIRING_MANAGER_EVALUATION:
                continue
            if not agent_result.succeeded or agent_result.output is None:
                return None
            recommendation = getattr(agent_result.output, "hire_recommendation", None)
            if isinstance(recommendation, HireRecommendation):
                return recommendation
            return None
        return None

    def _persist_judge_recommendations(
        self,
        run: EvaluationRun,
        judge_row: AgentEvaluation,
        judge: AgentExecutionResult,
        session_id: UUID,
        answer_id: UUID | None,
    ) -> None:
        output = judge.output
        assert output is not None
        for improvement in output.priority_improvements:
            self._session.add(
                ImprovementRecommendation(
                    evaluation_run_id=run.id,
                    agent_evaluation_id=judge_row.id,
                    session_id=session_id,
                    answer_id=answer_id,
                    priority=improvement.priority,
                    area=improvement.area,
                    recommendation_text=improvement.recommendation,
                    example_text=improvement.rationale,
                )
            )

    def _persist_coach_recommendation(
        self,
        run: EvaluationRun,
        coach_row: AgentEvaluation,
        coach: AgentExecutionResult,
        session_id: UUID,
        answer_id: UUID | None,
    ) -> None:
        output = coach.output
        assert output is not None
        focus = output.highest_priority
        self._session.add(
            ImprovementRecommendation(
                evaluation_run_id=run.id,
                agent_evaluation_id=coach_row.id,
                session_id=session_id,
                answer_id=answer_id,
                priority=1,
                area=focus.area,
                recommendation_text=focus.improvement,
                example_text=output.better_example_answer,
                action_items=[focus.specific_action],
                practice_plan=output.practice_exercise.model_dump(mode="json"),
            )
        )
