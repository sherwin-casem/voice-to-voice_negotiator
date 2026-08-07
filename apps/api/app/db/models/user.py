import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.context import JobDescription, Resume
    from app.db.models.evaluation import EvaluationRun
    from app.db.models.interview import InterviewConfiguration, InterviewSession
    from app.db.models.progress import UserProgressSnapshot


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped["UserProfile | None"] = relationship(back_populates="user", uselist=False)
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="user")
    job_descriptions: Mapped[list["JobDescription"]] = relationship(back_populates="user")
    interview_configurations: Mapped[list["InterviewConfiguration"]] = relationship(back_populates="user")
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(back_populates="user")
    progress_snapshots: Mapped[list["UserProgressSnapshot"]] = relationship(back_populates="user")


class UserProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(String(120))
    target_role: Mapped[str | None] = mapped_column(String(200))
    experience_level: Mapped[str | None] = mapped_column(String(50))
    timezone: Mapped[str | None] = mapped_column(String(64))
    preferences: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")

    user: Mapped["User"] = relationship(back_populates="profile")


class RefreshToken(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
