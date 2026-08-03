import asyncio
import logging
from datetime import UTC, datetime

from app.db.enums import AgentName, EvaluationRunStatus
from app.modules.evaluation.agents.base import BaseEvaluator
from app.modules.evaluation.interface import Evaluator
from app.modules.evaluation.schemas import AgentExecutionResult, EvaluationContext, EvaluationRunResult

logger = logging.getLogger(__name__)
ORCHESTRATION_VERSION = "1.0"


class EvaluationService:
    """Orchestrates specialist evaluators in parallel with isolated failure handling."""

    def __init__(
        self,
        evaluators: list[Evaluator],
        *,
        orchestration_version: str = ORCHESTRATION_VERSION,
    ) -> None:
        self._evaluators = evaluators
        self._orchestration_version = orchestration_version

    async def evaluate(self, context: EvaluationContext) -> EvaluationRunResult:
        started_at = datetime.now(UTC)

        tasks = [evaluator.evaluate(context) for evaluator in self._evaluators]
        agent_results: list[AgentExecutionResult] = list(await asyncio.gather(*tasks))

        completed_at = datetime.now(UTC)
        result = EvaluationRunResult(
            scope=context.scope,
            orchestration_version=self._orchestration_version,
            agent_results=agent_results,
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
                "skipped_agents": sum(1 for item in agent_results if item.skipped),
            },
        )
        return result

    async def evaluate_agent(
        self,
        agent_name: AgentName,
        context: EvaluationContext,
    ) -> AgentExecutionResult:
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
