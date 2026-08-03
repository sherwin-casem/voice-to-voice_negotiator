from pydantic import BaseModel, Field


class ParsedJobRequirements(BaseModel):
    """Structured JD stored in job_descriptions.parsed_requirements."""

    schema_version: str = Field(default="1.0", max_length=20)
    role_title: str | None = Field(default=None, max_length=200)
    experience_level: str | None = Field(default=None, max_length=50)
    required_skills: list[str] = Field(default_factory=list, max_length=30)
    preferred_skills: list[str] = Field(default_factory=list, max_length=30)
    responsibilities: list[str] = Field(default_factory=list, max_length=25)
    technical_topics: list[str] = Field(default_factory=list, max_length=20)
    behavioral_topics: list[str] = Field(default_factory=list, max_length=20)
    likely_interview_topics: list[str] = Field(default_factory=list, max_length=20)
    evaluation_rubric_hints: list[str] = Field(default_factory=list, max_length=15)
    summary_text: str = Field(min_length=10, max_length=5000)
