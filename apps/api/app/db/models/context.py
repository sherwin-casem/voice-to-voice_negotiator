import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enum_types import DocumentParseStatusEnum
from app.db.enums import DocumentParseStatus
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.interview import InterviewSession
    from app.db.models.user import User


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parse_status: Mapped[DocumentParseStatus] = mapped_column(
        DocumentParseStatusEnum,
        nullable=False,
        server_default=DocumentParseStatus.PENDING.value,
    )
    parsed_profile: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    summary_text: Mapped[str | None] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")

    user: Mapped["User"] = relationship(back_populates="resumes")
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(back_populates="resume")


class JobDescription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_descriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(200))
    source_filename: Mapped[str | None] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parse_status: Mapped[DocumentParseStatus] = mapped_column(
        DocumentParseStatusEnum,
        nullable=False,
        server_default=DocumentParseStatus.PENDING.value,
    )
    parsed_requirements: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    summary_text: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="job_descriptions")
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(back_populates="job_description")
