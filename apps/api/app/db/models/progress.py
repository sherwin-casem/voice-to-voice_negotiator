import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enum_types import InterviewTypeEnum
from app.db.enums import InterviewType
from app.db.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.evaluation import EvaluationRun
    from app.db.models.interview import InterviewSession
    from app.db.models.user import User


class UserProgressSnapshot(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "user_progress_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    interview_type: Mapped[InterviewType] = mapped_column(InterviewTypeEnum, nullable=False)
    overall_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    dimension_scores: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    sessions_completed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="progress_snapshots")
    session: Mapped["InterviewSession"] = relationship(back_populates="progress_snapshots")
    evaluation_run: Mapped["EvaluationRun"] = relationship(back_populates="progress_snapshots")
