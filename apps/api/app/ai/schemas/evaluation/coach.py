from pydantic import BaseModel, Field, field_validator


class PriorityCoachingFocus(BaseModel):
    """The single highest-priority improvement for the candidate."""

    area: str = Field(min_length=2, max_length=80)
    improvement: str = Field(
        min_length=30,
        max_length=800,
        description="Specific, evidence-based improvement guidance — not generic advice.",
    )
    why_it_matters: str = Field(min_length=20, max_length=600)
    specific_action: str = Field(min_length=20, max_length=600)


class PracticeExercise(BaseModel):
    title: str = Field(min_length=5, max_length=120)
    instructions: str = Field(min_length=30, max_length=1000)
    success_criteria: str = Field(min_length=20, max_length=500)


class ImprovementCoachOutput(BaseModel):
    """Actionable coaching feedback grounded in evaluation evidence."""

    did_well: list[str] = Field(min_length=1, max_length=5)
    should_improve: list[str] = Field(min_length=1, max_length=5)
    highest_priority: PriorityCoachingFocus
    better_example_answer: str | None = Field(default=None, max_length=2000)
    practice_exercise: PracticeExercise
    evidence_citations: list[str] = Field(default_factory=list, max_length=6)
    prompt_version: str = Field(default="1.0", max_length=20)
    summary: str = Field(min_length=30, max_length=1500)

    @field_validator("did_well", "should_improve")
    @classmethod
    def reject_generic_phrases(cls, values: list[str]) -> list[str]:
        banned = (
            "improve your communication",
            "be more confident",
            "practice more",
            "work on your answers",
        )
        for item in values:
            lowered = item.lower()
            for phrase in banned:
                if phrase in lowered and len(item) < 60:
                    raise ValueError(f"Feedback too generic: {item}")
        return values
