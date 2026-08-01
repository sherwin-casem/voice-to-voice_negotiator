from pydantic import BaseModel, Field

from app.db.enums import InterviewType


class PriorTurn(BaseModel):
    sequence_num: int
    question_text: str
    answer_text: str | None = None
    topic_tag: str | None = None


class InterviewerQuestionOutput(BaseModel):
    """Structured output schema for the Interviewer Agent."""

    question_text: str = Field(min_length=10, max_length=2000)
    topic_tag: str = Field(min_length=2, max_length=100)
    follow_up_intent: str | None = Field(default=None, max_length=200)
    is_follow_up: bool = False
    should_end_session: bool = False
    difficulty_adjustment: str | None = Field(
        default=None,
        description="Suggested adjustment: easier, same, or harder",
    )
    prompt_version: str = Field(default="1.0", max_length=20)


class InterviewerContext(BaseModel):
    interview_type: InterviewType
    difficulty: str
    target_role: str | None = None
    company_context: str | None = None
    resume_summary: str | None = None
    job_description_summary: str | None = None
    prior_turns: list[PriorTurn] = Field(default_factory=list)
    question_number: int = Field(ge=1)
    max_questions: int | None = None
    asked_topics: list[str] = Field(default_factory=list)
