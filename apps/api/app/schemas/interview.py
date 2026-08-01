from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.enums import InterviewSessionStatus, InterviewType


DifficultyLevel = Literal["junior", "mid", "senior"]


class CreateSessionRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class ConfigureSessionRequest(BaseModel):
    interview_type: InterviewType
    difficulty: DifficultyLevel
    target_role: str | None = Field(default=None, max_length=200)
    company_context: str | None = Field(default=None, max_length=2000)
    max_questions: int | None = Field(default=None, ge=1, le=50)
    target_duration_minutes: int | None = Field(default=None, ge=5, le=180)
    title: str | None = Field(default=None, max_length=200)
    resume_id: UUID | None = None
    job_description_id: UUID | None = None


class SubmitAnswerRequest(BaseModel):
    question_id: UUID
    answer_text: str = Field(min_length=1, max_length=20000)
    duration_ms: int | None = Field(default=None, ge=0)


class EndSessionRequest(BaseModel):
    reason: str = Field(default="user_ended", max_length=100)


class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: InterviewSessionStatus
    interview_type: InterviewType
    title: str | None
    config: dict
    question_count: int
    resume_id: UUID | None
    job_description_id: UUID | None
    started_at: datetime | None
    ended_at: datetime | None
    end_reason: str | None


class QuestionResponse(BaseModel):
    id: UUID
    session_id: UUID
    sequence_num: int
    question_text: str
    topic_tag: str | None
    follow_up_intent: str | None
    is_follow_up: bool
    asked_at: datetime
    agent_metadata: dict


class AnswerResponse(BaseModel):
    id: UUID
    session_id: UUID
    question_id: UUID
    answer_text: str
    answered_at: datetime
    duration_ms: int | None
    word_count: int | None


class QuestionResultResponse(BaseModel):
    session: SessionResponse
    question: QuestionResponse
    should_end_session: bool


class SubmitAnswerResponse(BaseModel):
    session: SessionResponse
    answer: AnswerResponse
