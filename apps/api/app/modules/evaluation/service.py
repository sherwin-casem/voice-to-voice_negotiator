import asyncio
import logging
from datetime import UTC, datetime

from app.db.enums import AgentName, EvaluationRunStatus
from app.modules.evaluation.agents.coach import ImprovementCoachAgent
from app.modules.evaluation.agents.judge import JudgeAgent
from app.modules.evaluation.interface import Evaluator
from app.modules.evaluation.schemas import AgentExecutionResult, CoachInput, EvaluationContext, EvaluationRunResult

logger = logging.getLogger(__name__)
ORCHESTRATION_VERSION = "1.3"


class EvaluationService:
    """Orchestrates specialist evaluators, scoring judge, and improvement coach."""

    def __init__(
        self,
        evaluators: list[Evaluator],
        judge: JudgeAgent,
        coach: ImprovementCoachAgent,
        *,
        orchestration_version: str = ORCHESTRATION_VERSION,
    ) -> None:
        self._evaluators = evaluators
        self._judge = judge
        self._coach = coach
        self._orchestration_version = orchestration_version

    async def evaluate(self, context: EvaluationContext) -> EvaluationRunResult:
        started_at = datetime.now(UTC)

        tasks = [evaluator.evaluate(context) for evaluator in self._evaluators]
        specialist_results: list[AgentExecutionResult] = list(await asyncio.gather(*tasks))

        judge_result = await self._judge.judge(context, specialist_results)

        coach_result: AgentExecutionResult | None = None
        if judge_result.succeeded and judge_result.output is not None:
            coach_input = CoachInput(
                context=context,
                specialist_results=specialist_results,
                judge_output=judge_result.output,  # type: ignore[arg-type]
                historical_weaknesses=context.historical_weaknesses,
            )
            coach_result = await self._coach.coach(coach_input)

        completed_at = datetime.now(UTC)
        result = EvaluationRunResult(
            scope=context.scope,
            orchestration_version=self._orchestration_version,
            agent_results=specialist_results,
            judge_result=judge_result,
            coach_result=coach_result,
            started_at=started_at,
            completed_at=completed_at,
        )

        logger.info(
            "Evaluation run completed",
            extra={
                "component": "evaluation",
                "scope": context.scope.value,
                "status": result.status.value,
                "successful_agents": len(result.successful_agents),
                "failed_agents": len(result.failed_agents),
                "skipped_agents": sum(1 for item in specialist_results if item.skipped),
                "judge_status": judge_result.status.value,
                "coach_status": coach_result.status.value if coach_result else None,
                "overall_score": (
                    judge_result.output.overall_score  # type: ignore[union-attr]
                    if judge_result.succeeded
                    else None
                ),
            },
        )
        return result

    async def evaluate_agent(
        self,
        agent_name: AgentName,
        context: EvaluationContext,
    ) -> AgentExecutionResult:
        # Judge and coach need the full specialist pass; a single specialist
        # request runs only that evaluator.
        if agent_name in {AgentName.SCORING_JUDGE, AgentName.IMPROVEMENT_COACH}:
            specialist_results = list(
                await asyncio.gather(
                    *(evaluator.evaluate(context) for evaluator in self._evaluators)
                )
            )

            if agent_name == AgentName.SCORING_JUDGE:
                return await self._judge.judge(context, specialist_results)

            judge_result = await self._judge.judge(context, specialist_results)
            if not judge_result.succeeded or judge_result.output is None:
                return AgentExecutionResult(
                    agent_name=agent_name,
                    status=EvaluationRunStatus.FAILED,
                    schema_version=self._coach.schema_version,
                    error_message="Judge evaluation must succeed before coaching",
                    started_at=datetime.now(UTC),
                    completed_at=datetime.now(UTC),
                )
            coach_input = CoachInput(
                context=context,
                specialist_results=specialist_results,
                judge_output=judge_result.output,  # type: ignore[arg-type]
                historical_weaknesses=context.historical_weaknesses,
            )
            return await self._coach.coach(coach_input)

        for evaluator in self._evaluators:
            if evaluator.agent_name == agent_name:
                return await evaluator.evaluate(context)
        return AgentExecutionResult(
            agent_name=agent_name,
            status=EvaluationRunStatus.FAILED,
            schema_version="unknown",
            error_message=f"Unknown evaluator: {agent_name.value}",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
