import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enum_types import (
    AgentNameEnum,
    EvaluationRunStatusEnum,
    EvaluationScopeEnum,
    HireRecommendationEnum,
)
from app.db.enums import AgentName, EvaluationRunStatus, EvaluationScope, HireRecommendation
from app.db.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.interview import CandidateAnswer, InterviewSession
    from app.db.models.progress import UserProgressSnapshot


class EvaluationRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        CheckConstraint(
            "(scope = 'session' AND answer_id IS NULL) OR "
            "(scope = 'answer' AND answer_id IS NOT NULL)",
            name="ck_evaluation_runs_scope_answer_id",
        ),
        Index("ix_evaluation_runs_session_id_scope", "session_id", "scope"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_answers.id", ondelete="CASCADE"),
        index=True,
    )
    scope: Mapped[EvaluationScope] = mapped_column(EvaluationScopeEnum, nullable=False)
    status: Mapped[EvaluationRunStatus] = mapped_column(
        EvaluationRunStatusEnum,
        nullable=False,
        server_default=EvaluationRunStatus.PENDING.value,
        index=True,
    )
    trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    orchestration_version: Mapped[str] = mapped_column(String(20), nullable=False, server_default="1.0")
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session: Mapped["InterviewSession"] = relationship(back_populates="evaluation_runs")
    answer: Mapped["CandidateAnswer | None"] = relationship(back_populates="evaluation_runs")
    agent_evaluations: Mapped[list["AgentEvaluation"]] = relationship(back_populates="evaluation_run")
    evaluation_scores: Mapped[list["EvaluationScore"]] = relationship(back_populates="evaluation_run")
    evaluation_result: Mapped["EvaluationResult | None"] = relationship(
        back_populates="evaluation_run",
        uselist=False,
    )
    improvement_recommendations: Mapped[list["ImprovementRecommendation"]] = relationship(
        back_populates="evaluation_run",
    )
    progress_snapshots: Mapped[list["UserProgressSnapshot"]] = relationship(back_populates="evaluation_run")


class AgentEvaluation(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "agent_evaluations"
    __table_args__ = (
        UniqueConstraint("evaluation_run_id", "agent_name", name="uq_agent_evaluations_run_agent"),
    )

    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[AgentName] = mapped_column(AgentNameEnum, nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[EvaluationRunStatus] = mapped_column(
        EvaluationRunStatusEnum,
        nullable=False,
        server_default=EvaluationRunStatus.PENDING.value,
    )
    skipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    skip_reason: Mapped[str | None] = mapped_column(String(200))
    model_id: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(50))
    summary: Mapped[str | None] = mapped_column(Text)
    output: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    evaluation_run: Mapped["EvaluationRun"] = relationship(back_populates="agent_evaluations")
    evaluation_scores: Mapped[list["EvaluationScore"]] = relationship(back_populates="agent_evaluation")
    improvement_recommendations: Mapped[list["ImprovementRecommendation"]] = relationship(
        back_populates="agent_evaluation",
    )


class EvaluationScore(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "evaluation_scores"
    __table_args__ = (
        UniqueConstraint("agent_evaluation_id", "dimension_key", name="uq_evaluation_scores_agent_dimension"),
    )

    agent_evaluation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_evaluations.id", ondelete="CASCADE"),
        nullable=False,
    )
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_answers.id", ondelete="CASCADE"),
        index=True,
    )
    agent_name: Mapped[AgentName] = mapped_column(AgentNameEnum, nullable=False, index=True)
    dimension_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    max_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, server_default="100")
    normalized_score: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        Computed("score / NULLIF(max_score, 0) * 100", persisted=True),
        nullable=False,
    )
    weight: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    evidence: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")

    agent_evaluation: Mapped["AgentEvaluation"] = relationship(back_populates="evaluation_scores")
    evaluation_run: Mapped["EvaluationRun"] = relationship(back_populates="evaluation_scores")


class EvaluationResult(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "evaluation_results"

    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_answers.id", ondelete="CASCADE"),
    )
    overall_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, index=True)
    overall_max: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, server_default="100")
    hire_recommendation: Mapped[HireRecommendation | None] = mapped_column(HireRecommendationEnum)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    dimension_scores: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    weights_applied: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    key_strengths: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    key_gaps: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    judge_output: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")

    evaluation_run: Mapped["EvaluationRun"] = relationship(back_populates="evaluation_result")


class ImprovementRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "improvement_recommendations"

    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_evaluations.id", ondelete="SET NULL"),
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_answers.id", ondelete="SET NULL"),
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    area: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    example_text: Mapped[str | None] = mapped_column(Text)
    action_items: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    practice_plan: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    evaluation_run: Mapped["EvaluationRun"] = relationship(back_populates="improvement_recommendations")
    agent_evaluation: Mapped["AgentEvaluation | None"] = relationship(back_populates="improvement_recommendations")
