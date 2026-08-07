from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import BaseModel

from app.ai.types import TokenUsage
from app.db.enums import AgentName, EvaluationRunStatus, EvaluationScope, InterviewType

if TYPE_CHECKING:
    from app.ai.schemas.evaluation.judge import JudgeEvaluationOutput

@dataclass(frozen=True)
class ConversationTurn:
    sequence_num: int
    question_text: str
    answer_text: str
    topic_tag: str | None = None


@dataclass(frozen=True)
class CandidateProfile:
    """Optional candidate background used by the improvement coach."""

    summary: str | None = None
    target_role: str | None = None
    experience_level: str | None = None


@dataclass(frozen=True)
class EvaluationContext:
    """Structured input shared by all specialist evaluators."""

    interview_type: InterviewType
    difficulty: str
    question_text: str
    answer_text: str
    scope: EvaluationScope = EvaluationScope.ANSWER
    target_role: str | None = None
    company_context: str | None = None
    resume_summary: str | None = None
    job_description_summary: str | None = None
    topic_tag: str | None = None
    prior_turns: list[ConversationTurn] = field(default_factory=list)
    session_id: UUID | None = None
    answer_id: UUID | None = None
    candidate_profile: CandidateProfile | None = None
    historical_weaknesses: list[str] = field(default_factory=list)
    candidate_skills: list[str] = field(default_factory=list)
    relevant_experience: list[str] = field(default_factory=list)
    role_responsibilities: list[str] = field(default_factory=list)
    technical_focus_areas: list[str] = field(default_factory=list)
    behavioral_focus_areas: list[str] = field(default_factory=list)
    evaluation_rubric_hints: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AgentExecutionResult:
    agent_name: AgentName
    status: EvaluationRunStatus
    schema_version: str
    skipped: bool = False
    skip_reason: str | None = None
    output: BaseModel | None = None
    model_id: str | None = None
    prompt_version: str | None = None
    latency_ms: int | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    token_usage: TokenUsage | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == EvaluationRunStatus.COMPLETED and self.output is not None

    def to_metadata_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name.value,
            "status": self.status.value,
            "schema_version": self.schema_version,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
            "latency_ms": self.latency_ms,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass(frozen=True)
class CoachInput:
    """Inputs for the improvement coach after specialist and judge evaluation."""

    context: EvaluationContext
    specialist_results: list[AgentExecutionResult]
    judge_output: "JudgeEvaluationOutput"
    historical_weaknesses: list[str] = field(default_factory=list)

    @property
    def candidate_profile(self) -> CandidateProfile | None:
        return self.context.candidate_profile


@dataclass(frozen=True)
class EvaluationRunResult:
    scope: EvaluationScope
    orchestration_version: str
    agent_results: list[AgentExecutionResult]
    started_at: datetime
    completed_at: datetime
    judge_result: AgentExecutionResult | None = None
    coach_result: AgentExecutionResult | None = None

    @property
    def status(self) -> EvaluationRunStatus:
        if self.agent_results and all(result.skipped for result in self.agent_results):
            return EvaluationRunStatus.SKIPPED
        # A run is only COMPLETED when the judge produced a final evaluation;
        # specialist output without a judge rollup is not a usable result.
        if (
            self.judge_result is not None
            and self.judge_result.succeeded
            and any(result.succeeded for result in self.agent_results)
        ):
            return EvaluationRunStatus.COMPLETED
        return EvaluationRunStatus.FAILED

    @property
    def successful_agents(self) -> list[AgentExecutionResult]:
        return [result for result in self.agent_results if result.succeeded]

    @property
    def failed_agents(self) -> list[AgentExecutionResult]:
        return [
            result
            for result in self.agent_results
            if result.status == EvaluationRunStatus.FAILED
        ]
