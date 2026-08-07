import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar

from pydantic import BaseModel

from app.ai.providers.base import StructuredOutputProvider
from app.ai.schemas.evaluation.common import DimensionScore
from app.ai.usage import consume_token_usage
from app.db.enums import AgentName, EvaluationRunStatus
from app.modules.evaluation.schemas import AgentExecutionResult, EvaluationContext

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)
MessageBuilder = Callable[[EvaluationContext], list[dict[str, str]]]
GatingFn = Callable[[EvaluationContext], tuple[bool, str | None]]


class BaseEvaluator:
    """Specialist evaluator that calls structured LLM output and never touches persistence."""

    def __init__(
        self,
        *,
        agent_name: AgentName,
        output_schema: type[T],
        schema_version: str,
        prompt_version: str,
        build_messages: MessageBuilder,
        should_run_fn: GatingFn,
        llm_provider: StructuredOutputProvider,
        model_id: str,
    ) -> None:
        self.agent_name = agent_name
        self.output_schema = output_schema
        self.schema_version = schema_version
        self.prompt_version = prompt_version
        self._build_messages = build_messages
        self._should_run_fn = should_run_fn
        self._llm = llm_provider
        self._model_id = model_id

    def should_run(self, context: EvaluationContext) -> tuple[bool, str | None]:
        return self._should_run_fn(context)

    async def evaluate(self, context: EvaluationContext) -> AgentExecutionResult:
        started_at = datetime.now(UTC)
        start_ms = time.perf_counter()

        should_run, skip_reason = self.should_run(context)
        if not should_run:
            completed_at = datetime.now(UTC)
            return AgentExecutionResult(
                agent_name=self.agent_name,
                status=EvaluationRunStatus.SKIPPED,
                schema_version=self.schema_version,
                skipped=True,
                skip_reason=skip_reason,
                model_id=self._model_id,
                prompt_version=self.prompt_version,
                latency_ms=int((time.perf_counter() - start_ms) * 1000),
                started_at=started_at,
                completed_at=completed_at,
            )

        try:
            messages = self._build_messages(context)
            output = await self._llm.generate_structured(
                messages,
                self.output_schema,
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
        except Exception as exc:  # noqa: BLE001 — isolate agent failures
            logger.exception(
                "Evaluator agent failed",
                extra={
                    "component": "evaluation",
                    "agent_name": self.agent_name.value,
                },
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


def _dimension(score: float, rationale: str, evidence: list[str] | None = None) -> DimensionScore:
    return DimensionScore(
        score=score,
        rationale=rationale,
        evidence=evidence or ["Mock evidence from automated evaluation."],
    )
