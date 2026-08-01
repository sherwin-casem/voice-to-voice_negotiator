from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
    created_at: datetime


class JobDescriptionResponse(BaseModel):
    id: UUID
    title: str
    company_name: str | None
    summary_text: str | None
    created_at: datetime
