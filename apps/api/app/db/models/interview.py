import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enum_types import InterviewSessionStatusEnum, InterviewTypeEnum
from app.db.enums import InterviewSessionStatus, InterviewType
from app.db.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.context import JobDescription, Resume
    from app.db.models.evaluation import EvaluationRun
    from app.db.models.progress import UserProgressSnapshot
    from app.db.models.transcript import SessionTranscript, TranscriptSegment
    from app.db.models.user import User


class InterviewConfiguration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interview_configurations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    interview_type: Mapped[InterviewType] = mapped_column(InterviewTypeEnum, nullable=False)
    target_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    max_questions: Mapped[int | None] = mapped_column(Integer)
    difficulty: Mapped[str | None] = mapped_column(String(50))
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    is_template: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")

    user: Mapped["User"] = relationship(back_populates="interview_configurations")
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(back_populates="configuration")


class InterviewSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interview_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    configuration_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_configurations.id", ondelete="SET NULL"),
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
    )
    job_description_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_descriptions.id", ondelete="SET NULL"),
    )
    status: Mapped[InterviewSessionStatus] = mapped_column(
        InterviewSessionStatusEnum,
        nullable=False,
        server_default=InterviewSessionStatus.CREATED.value,
        index=True,
    )
    interview_type: Mapped[InterviewType] = mapped_column(InterviewTypeEnum, nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    config_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_reason: Mapped[str | None] = mapped_column(String(100))

    user: Mapped["User"] = relationship(back_populates="interview_sessions")
    configuration: Mapped["InterviewConfiguration | None"] = relationship(back_populates="interview_sessions")
    resume: Mapped["Resume | None"] = relationship(back_populates="interview_sessions")
    job_description: Mapped["JobDescription | None"] = relationship(back_populates="interview_sessions")
    questions: Mapped[list["InterviewQuestion"]] = relationship(
        back_populates="session",
        order_by="InterviewQuestion.sequence_num",
    )
    answers: Mapped[list["CandidateAnswer"]] = relationship(back_populates="session")
    transcript_segments: Mapped[list["TranscriptSegment"]] = relationship(back_populates="session")
    session_transcript: Mapped["SessionTranscript | None"] = relationship(back_populates="session", uselist=False)
    evaluation_runs: Mapped[list["EvaluationRun"]] = relationship(back_populates="session")
    progress_snapshots: Mapped[list["UserProgressSnapshot"]] = relationship(back_populates="session")


class InterviewQuestion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "interview_questions"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence_num", name="uq_interview_questions_session_sequence"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_num: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    topic_tag: Mapped[str | None] = mapped_column(String(100))
    follow_up_intent: Mapped[str | None] = mapped_column(String(200))
    is_follow_up: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    parent_question_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="SET NULL"),
    )
    agent_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped["InterviewSession"] = relationship(back_populates="questions")
    parent_question: Mapped["InterviewQuestion | None"] = relationship(
        remote_side="InterviewQuestion.id",
        back_populates="follow_ups",
    )
    follow_ups: Mapped[list["InterviewQuestion"]] = relationship(back_populates="parent_question")
    answer: Mapped["CandidateAnswer | None"] = relationship(back_populates="question", uselist=False)
    transcript_segments: Mapped[list["TranscriptSegment"]] = relationship(back_populates="question")


class CandidateAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidate_answers"

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    stt_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    audio_storage_key: Mapped[str | None] = mapped_column(String(500))
    word_count: Mapped[int | None] = mapped_column(Integer)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped["InterviewSession"] = relationship(back_populates="answers")
    question: Mapped["InterviewQuestion"] = relationship(back_populates="answer")
    transcript_segments: Mapped[list["TranscriptSegment"]] = relationship(back_populates="answer")
    evaluation_runs: Mapped[list["EvaluationRun"]] = relationship(back_populates="answer")
