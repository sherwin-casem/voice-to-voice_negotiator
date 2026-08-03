import logging
import time
from datetime import UTC, datetime

from app.ai.prompts.evaluation.judge.v1.builder import (
    PROMPT_VERSION,
    SCHEMA_VERSION,
    build_judge_messages,
    merge_judge_output,
)
from app.ai.providers.base import StructuredOutputProvider
from app.ai.schemas.evaluation.judge import (
    EvidenceItem,
    JudgeEvaluationOutput,
    JudgeSynthesisOutput,
    PriorityImprovement,
)
from app.db.enums import AgentName, EvaluationRunStatus
from app.modules.evaluation.judge.scoring_model import METHODOLOGY_VERSION, ScoringBaseline, ScoringModel
from app.modules.evaluation.mock_llm import MockEvaluationLLMProvider, build_mock_judge_synthesis
from app.modules.evaluation.schemas import AgentExecutionResult, EvaluationContext

logger = logging.getLogger(__name__)


class JudgeAgent:
    """Rolls up specialist outputs into a final structured evaluation."""

    agent_name = AgentName.SCORING_JUDGE
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

    async def judge(
        self,
        context: EvaluationContext,
        specialist_results: list[AgentExecutionResult],
    ) -> AgentExecutionResult:
        started_at = datetime.now(UTC)
        start_ms = time.perf_counter()

        if not any(result.succeeded for result in specialist_results):
            completed_at = datetime.now(UTC)
            return AgentExecutionResult(
                agent_name=self.agent_name,
                status=EvaluationRunStatus.FAILED,
                schema_version=self.schema_version,
                model_id=self._model_id,
                prompt_version=self.prompt_version,
                latency_ms=int((time.perf_counter() - start_ms) * 1000),
                error_message="No successful specialist evaluations available for judging",
                started_at=started_at,
                completed_at=completed_at,
            )

        baseline = ScoringModel.compute(context, specialist_results)

        try:
            if isinstance(self._llm, MockEvaluationLLMProvider):
                synthesis = build_mock_judge_synthesis(context, baseline)
            else:
                messages = build_judge_messages(context, specialist_results, baseline)
                synthesis = await self._llm.generate_structured(
                    messages,
                    JudgeSynthesisOutput,
                    model=self._model_id,
                )
                synthesis = synthesis.model_copy(update={"prompt_version": self.prompt_version})

            output = merge_judge_output(baseline, synthesis, prompt_version=self.prompt_version)
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
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Judge agent failed; returning baseline-only fallback",
                extra={"component": "evaluation", "agent_name": self.agent_name.value},
            )
            fallback = _baseline_fallback_output(context, baseline)
            completed_at = datetime.now(UTC)
            return AgentExecutionResult(
                agent_name=self.agent_name,
                status=EvaluationRunStatus.COMPLETED,
                schema_version=self.schema_version,
                output=fallback,
                model_id=self._model_id,
                prompt_version=self.prompt_version,
                latency_ms=int((time.perf_counter() - start_ms) * 1000),
                error_message=f"Synthesis failed, baseline fallback used: {exc}",
                started_at=started_at,
                completed_at=completed_at,
            )


def _baseline_fallback_output(
    context: EvaluationContext,
    baseline: ScoringBaseline,
) -> JudgeEvaluationOutput:
    excerpt = context.answer_text[:120].strip()
    if len(context.answer_text) > 120:
        excerpt += "..."

    return JudgeEvaluationOutput(
        overall_score=baseline.overall_score,
        dimension_scores=baseline.dimension_scores,
        strengths=[f"Strongest areas: {', '.join(baseline.strongest_dimensions)}"],
        weaknesses=[f"Weakest areas: {', '.join(baseline.weakest_dimensions)}"],
        evidence=[
            EvidenceItem(
                quote=excerpt or context.answer_text,
                dimension=baseline.weakest_dimensions[0]
                if baseline.weakest_dimensions
                else "general",
                supports="weakness" if baseline.overall_score < 60 else "strength",
            )
        ],
        priority_improvements=[
            PriorityImprovement(
                area=baseline.weakest_dimensions[0]
                if baseline.weakest_dimensions
                else "communication",
                priority=1,
                recommendation="Focus practice on the weakest scored dimension.",
                rationale="Derived from scoring model baseline after synthesis failure.",
            )
        ],
        strongest_dimensions=baseline.strongest_dimensions,
        weakest_dimensions=baseline.weakest_dimensions,
        conflict_resolutions=baseline.conflict_resolutions,
        weights_applied=baseline.weights_applied,
        scoring_methodology_version=METHODOLOGY_VERSION,
        prompt_version=PROMPT_VERSION,
        summary=(
            f"Baseline evaluation score {baseline.overall_score}/100 based on available specialist outputs."
        ),
    )
