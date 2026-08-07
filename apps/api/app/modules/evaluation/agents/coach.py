import logging
import time
from datetime import UTC, datetime

from app.ai.prompts.evaluation.coach.v1.builder import PROMPT_VERSION, SCHEMA_VERSION, build_coach_messages
from app.ai.providers.base import StructuredOutputProvider
from app.ai.schemas.evaluation.coach import ImprovementCoachOutput
from app.ai.usage import consume_token_usage
from app.ai.schemas.evaluation.judge import JudgeEvaluationOutput
from app.db.enums import AgentName, EvaluationRunStatus
from app.modules.evaluation.mock_llm import MockEvaluationLLMProvider, build_mock_coach_output
from app.modules.evaluation.schemas import AgentExecutionResult, CoachInput

logger = logging.getLogger(__name__)


class ImprovementCoachAgent:
    """Generates actionable, evidence-based coaching from evaluation results."""

    agent_name = AgentName.IMPROVEMENT_COACH
    schema_version = SCHEMA_VERSION
    prompt_version = PROMPT_VERSION

    def __init__(
        self,
        llm_provider: StructuredOutputProvider | MockEvaluationLLMProvider,
        *,
        model_id: str,
    ) -> None:
        self._llm = llm_provider
        self._model_id = model_id

    async def coach(self, coach_input: CoachInput) -> AgentExecutionResult:
        started_at = datetime.now(UTC)
        start_ms = time.perf_counter()

        judge_output = coach_input.judge_output
        if not isinstance(judge_output, JudgeEvaluationOutput):
            completed_at = datetime.now(UTC)
            return AgentExecutionResult(
                agent_name=self.agent_name,
                status=EvaluationRunStatus.FAILED,
                schema_version=self.schema_version,
                model_id=self._model_id,
                prompt_version=self.prompt_version,
                latency_ms=int((time.perf_counter() - start_ms) * 1000),
                error_message="Judge evaluation output is required for coaching",
                started_at=started_at,
                completed_at=completed_at,
            )

        try:
            if isinstance(self._llm, MockEvaluationLLMProvider):
                output = build_mock_coach_output(coach_input)
            else:
                messages = build_coach_messages(coach_input)
                output = await self._llm.generate_structured(
                    messages,
                    ImprovementCoachOutput,
                    model=self._model_id,
                )
                output = output.model_copy(update={"prompt_version": self.prompt_version})

            completed_at = datetime.now(UTC)
            return AgentExecutionResult(
                agent_name=self.agent_name,
                status=EvaluationRunStatus.COMPLETED,
                schema_version=self.schema_version,
                output=output,
                model_id=self._model_id,
                prompt_version=self.prompt_version,
                latency_ms=int((time.perf_counter() - start_ms) * 1000),
                started_at=started_at,
                completed_at=completed_at,
                token_usage=consume_token_usage(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Improvement coach failed",
                extra={"component": "evaluation", "agent_name": self.agent_name.value},
            )
            completed_at = datetime.now(UTC)
            return AgentExecutionResult(
                agent_name=self.agent_name,
                status=EvaluationRunStatus.FAILED,
                schema_version=self.schema_version,
                model_id=self._model_id,
                prompt_version=self.prompt_version,
                latency_ms=int((time.perf_counter() - start_ms) * 1000),
                error_message=str(exc),
                started_at=started_at,
                completed_at=completed_at,
            )
