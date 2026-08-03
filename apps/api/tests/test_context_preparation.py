import pytest

from app.ai.schemas.context import ParsedJobRequirements, ParsedResumeProfile
from app.modules.context.extractor import HeuristicContextExtractor
from app.modules.context.schemas import InterviewStep, PreparedContextBundle
from app.modules.context.selector import ContextSelector


@pytest.mark.asyncio
async def test_heuristic_resume_extractor_identifies_skills_and_topics() -> None:
    extractor = HeuristicContextExtractor()
    raw_text = """
    Jane Doe
    Skills:
    - Python
    - PostgreSQL
    - System design
    Experience:
    - Senior Engineer at Acme Corp
    - Built a payments platform handling 10M daily transactions
    """

    profile = await extractor.extract_resume(raw_text, title="Jane Doe Resume")

    assert "Python" in profile.skills
    assert profile.experience
    assert profile.likely_interview_topics
    assert len(profile.summary_text) >= 10


@pytest.mark.asyncio
async def test_heuristic_job_description_extractor_identifies_rubric_hints() -> None:
    extractor = HeuristicContextExtractor()
    raw_text = """
    Senior Backend Engineer
    Requirements:
    - Python
    - AWS
    - Distributed systems
    Responsibilities:
    - Design scalable APIs
    - Mentor junior engineers
    """

    requirements = await extractor.extract_job_description(
        raw_text,
        title="Senior Backend Engineer",
        company_name="Acme",
    )

    assert "Python" in requirements.required_skills
    assert requirements.responsibilities
    assert requirements.evaluation_rubric_hints
    assert requirements.technical_topics


def test_selector_limits_opening_context_size() -> None:
    selector = ContextSelector()
    bundle = PreparedContextBundle(
        resume_profile=ParsedResumeProfile(
            summary_text="Backend engineer with platform experience.",
            skills=[f"Skill-{index}" for index in range(20)],
            likely_interview_topics=[f"Topic-{index}" for index in range(15)],
        ),
        job_requirements=ParsedJobRequirements(
            summary_text="Senior backend role requiring Python and AWS.",
            required_skills=[f"Req-{index}" for index in range(20)],
            responsibilities=[f"Resp-{index}" for index in range(20)],
            technical_topics=["API design", "Observability"],
            behavioral_topics=["Leadership", "Communication"],
            evaluation_rubric_hints=["Assess depth", "Assess impact"],
            likely_interview_topics=["Scaling", "Reliability"],
        ),
        difficulty="senior",
        interview_type="technical",
    )

    selected = selector.select(bundle, InterviewStep.INTERVIEWER_OPENING)

    assert len(selected.candidate_skills) <= 8
    assert len(selected.likely_interview_topics) <= 8
    assert selected.resume_summary is not None
    assert len(selected.resume_summary) <= 600


def test_selector_follow_up_prioritizes_current_topic() -> None:
    selector = ContextSelector()
    bundle = PreparedContextBundle(
        resume_profile=ParsedResumeProfile(
            summary_text="Engineer with Python and AWS experience.",
            skills=["Python", "AWS", "Leadership"],
            projects=[],
        ),
        job_requirements=ParsedJobRequirements(
            summary_text="Backend role.",
            required_skills=["Python"],
        ),
    )

    selected = selector.select(
        bundle,
        InterviewStep.INTERVIEWER_FOLLOW_UP,
        asked_topics={"python"},
        current_topic_tag="python",
        prior_answer_text="I used Python to optimize API latency.",
    )

    assert "Python" in selected.candidate_skills[0] or "Python" in selected.candidate_skills


def test_selector_evaluation_rubric_emphasizes_technical_topics_for_technical_interviews() -> None:
    selector = ContextSelector()
    bundle = PreparedContextBundle(
        job_requirements=ParsedJobRequirements(
            summary_text="Technical backend role.",
            technical_topics=["Distributed systems", "Caching", "Observability"],
            behavioral_topics=["Conflict resolution", "Mentorship", "Stakeholder management"],
            evaluation_rubric_hints=["Depth", "Trade-offs"],
        ),
        interview_type="technical",
    )

    selected = selector.select(bundle, InterviewStep.EVALUATION_RUBRIC)

    assert len(selected.technical_focus_areas) >= len(selected.behavioral_focus_areas)
    assert selected.evaluation_rubric_hints
