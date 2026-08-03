from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.enums import DocumentParseStatus


class CreateResumeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    raw_text: str = Field(min_length=1, max_length=100000)
    summary_text: str | None = Field(default=None, max_length=5000)


class CreateJobDescriptionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    raw_text: str = Field(min_length=1, max_length=100000)
    company_name: str | None = Field(default=None, max_length=200)
    summary_text: str | None = Field(default=None, max_length=5000)


class ResumeResponse(BaseModel):
    id: UUID
    title: str
    summary_text: str | None
    parse_status: DocumentParseStatus
    created_at: datetime


class JobDescriptionResponse(BaseModel):
    id: UUID
    title: str
    company_name: str | None
    summary_text: str | None
    parse_status: DocumentParseStatus
    created_at: datetime


class ParsedProfileSummary(BaseModel):
    skills: list[str] = Field(default_factory=list)
    experience_count: int = 0
    project_count: int = 0
    likely_interview_topics: list[str] = Field(default_factory=list)


class ParsedRequirementsSummary(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    technical_topics: list[str] = Field(default_factory=list)
    behavioral_topics: list[str] = Field(default_factory=list)
    likely_interview_topics: list[str] = Field(default_factory=list)
    evaluation_rubric_hints: list[str] = Field(default_factory=list)


class PreparedResumeResponse(ResumeResponse):
    parsed_profile: ParsedProfileSummary = Field(default_factory=ParsedProfileSummary)


class PreparedJobDescriptionResponse(JobDescriptionResponse):
    parsed_requirements: ParsedRequirementsSummary = Field(default_factory=ParsedRequirementsSummary)
