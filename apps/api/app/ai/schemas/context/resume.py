from pydantic import BaseModel, Field


class ExperienceEntry(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    duration: str | None = Field(default=None, max_length=100)
    highlights: list[str] = Field(default_factory=list, max_length=8)


class ProjectEntry(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=500)
    technologies: list[str] = Field(default_factory=list, max_length=10)


class ParsedResumeProfile(BaseModel):
    """Structured resume profile stored in resumes.parsed_profile."""

    schema_version: str = Field(default="1.0", max_length=20)
    headline: str | None = Field(default=None, max_length=300)
    years_experience: int | None = Field(default=None, ge=0, le=60)
    skills: list[str] = Field(default_factory=list, max_length=40)
    experience: list[ExperienceEntry] = Field(default_factory=list, max_length=12)
    projects: list[ProjectEntry] = Field(default_factory=list, max_length=12)
    responsibilities: list[str] = Field(default_factory=list, max_length=20)
    likely_interview_topics: list[str] = Field(default_factory=list, max_length=20)
    summary_text: str = Field(min_length=10, max_length=5000)
