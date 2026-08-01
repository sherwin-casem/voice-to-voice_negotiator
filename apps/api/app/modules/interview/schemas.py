from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.db.enums import InterviewSessionStatus, InterviewType


@dataclass(frozen=True)
class SessionConfigInput:
    interview_type: InterviewType
    difficulty: str
    target_role: str | None = None
    company_context: str | None = None
    max_questions: int | None = None
    target_duration_minutes: int | None = None
    title: str | None = None
    resume_id: UUID | None = None
    job_description_id: UUID | None = None


@dataclass(frozen=True)
class QuestionRecord:
    id: UUID
    session_id: UUID
    sequence_num: int
    question_text: str
    topic_tag: str | None
    follow_up_intent: str | None
    is_follow_up: bool
    asked_at: datetime
    agent_metadata: dict[str, Any]


@dataclass(frozen=True)
class AnswerRecord:
    id: UUID
    session_id: UUID
    question_id: UUID
    answer_text: str
    answered_at: datetime
    duration_ms: int | None = None
    word_count: int | None = None


@dataclass(frozen=True)
class SessionRecord:
    id: UUID
    user_id: UUID
    status: InterviewSessionStatus
    interview_type: InterviewType
    title: str | None
    config_snapshot: dict[str, Any]
    question_count: int
    resume_id: UUID | None
    job_description_id: UUID | None
    started_at: datetime | None
    ended_at: datetime | None
    end_reason: str | None


@dataclass(frozen=True)
class ContextSummaries:
    resume_summary: str | None
    job_description_summary: str | None
    company_name: str | None
