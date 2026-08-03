from enum import StrEnum

from app.ai.schemas.context import ParsedJobRequirements, ParsedResumeProfile


class InterviewStep(StrEnum):
    """Interview pipeline step used for context selection."""

    INTERVIEWER_OPENING = "interviewer_opening"
    INTERVIEWER_FOLLOW_UP = "interviewer_follow_up"
    EVALUATION_ANSWER = "evaluation_answer"
    EVALUATION_RUBRIC = "evaluation_rubric"
    COACH = "coach"


class PreparedContextBundle:
    """Fully parsed resume and job description data for a session."""

    __slots__ = (
        "resume_profile",
        "job_requirements",
        "company_name",
        "target_role",
        "interview_type",
        "difficulty",
    )

    def __init__(
        self,
        *,
        resume_profile: ParsedResumeProfile | None = None,
        job_requirements: ParsedJobRequirements | None = None,
        company_name: str | None = None,
        target_role: str | None = None,
        interview_type: str | None = None,
        difficulty: str | None = None,
    ) -> None:
        self.resume_profile = resume_profile
        self.job_requirements = job_requirements
        self.company_name = company_name
        self.target_role = target_role
        self.interview_type = interview_type
        self.difficulty = difficulty


class StepContext:
    """Compact, step-specific context slice for LLM prompts."""

    __slots__ = (
        "resume_summary",
        "job_description_summary",
        "candidate_skills",
        "relevant_experience",
        "relevant_projects",
        "role_responsibilities",
        "technical_focus_areas",
        "behavioral_focus_areas",
        "likely_interview_topics",
        "evaluation_rubric_hints",
        "suggested_difficulty",
    )

    def __init__(
        self,
        *,
        resume_summary: str | None = None,
        job_description_summary: str | None = None,
        candidate_skills: list[str] | None = None,
        relevant_experience: list[str] | None = None,
        relevant_projects: list[str] | None = None,
        role_responsibilities: list[str] | None = None,
        technical_focus_areas: list[str] | None = None,
        behavioral_focus_areas: list[str] | None = None,
        likely_interview_topics: list[str] | None = None,
        evaluation_rubric_hints: list[str] | None = None,
        suggested_difficulty: str | None = None,
    ) -> None:
        self.resume_summary = resume_summary
        self.job_description_summary = job_description_summary
        self.candidate_skills = candidate_skills or []
        self.relevant_experience = relevant_experience or []
        self.relevant_projects = relevant_projects or []
        self.role_responsibilities = role_responsibilities or []
        self.technical_focus_areas = technical_focus_areas or []
        self.behavioral_focus_areas = behavioral_focus_areas or []
        self.likely_interview_topics = likely_interview_topics or []
        self.evaluation_rubric_hints = evaluation_rubric_hints or []
        self.suggested_difficulty = suggested_difficulty
