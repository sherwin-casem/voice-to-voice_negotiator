import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enum_types import SpeakerRoleEnum
from app.db.enums import SpeakerRole
from app.db.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.interview import CandidateAnswer, InterviewQuestion, InterviewSession


class TranscriptSegment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "transcript_segments"

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="SET NULL"),
    )
    answer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_answers.id", ondelete="SET NULL"),
        index=True,
    )
    speaker: Mapped[SpeakerRole] = mapped_column(SpeakerRoleEnum, nullable=False)
    sequence_num: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    start_ms: Mapped[int | None] = mapped_column(Integer)
    end_ms: Mapped[int | None] = mapped_column(Integer)

    session: Mapped["InterviewSession"] = relationship(back_populates="transcript_segments")
    question: Mapped["InterviewQuestion | None"] = relationship(back_populates="transcript_segments")
    answer: Mapped["CandidateAnswer | None"] = relationship(back_populates="transcript_segments")


class SessionTranscript(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "session_transcripts"

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    structured_transcript: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped["InterviewSession"] = relationship(back_populates="session_transcript")
