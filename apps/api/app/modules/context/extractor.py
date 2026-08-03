import re

from app.ai.prompts.context.extractor.v1.builder import (
    build_job_description_extraction_messages,
    build_resume_extraction_messages,
)
from app.ai.providers.base import StructuredOutputProvider
from app.ai.schemas.context import ParsedJobRequirements, ParsedResumeProfile
from app.ai.schemas.context.resume import ExperienceEntry, ProjectEntry
from app.modules.context.repository import _bullet_items, _lines


class HeuristicContextExtractor:
    """Deterministic extraction for tests and mock AI provider mode."""

    _SKILL_HINTS = (
        "python",
        "java",
        "typescript",
        "javascript",
        "react",
        "aws",
        "kubernetes",
        "postgresql",
        "leadership",
        "communication",
        "system design",
    )

    async def extract_resume(self, raw_text: str, *, title: str) -> ParsedResumeProfile:
        lines = _lines(raw_text)
        bullets = _bullet_items(lines)

        skills = [item for item in bullets if len(item) <= 60][:12]
        if not skills:
            skills = [
                hint.title()
                for hint in self._SKILL_HINTS
                if hint in raw_text.lower()
            ][:8]
        if not skills:
            skills = ["Communication", "Problem solving"]

        experience: list[ExperienceEntry] = []
        for line in lines:
            if " at " in line.lower() and len(line) <= 120:
                parts = re.split(r"\s+at\s+", line, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) == 2:
                    experience.append(
                        ExperienceEntry(
                            title=parts[0].strip(),
                            company=parts[1].strip(),
                            highlights=bullets[:2],
                        )
                    )
        if not experience and lines:
            experience.append(
                ExperienceEntry(
                    title=title,
                    company=None,
                    highlights=bullets[:3] or ["Delivered projects end-to-end"],
                )
            )

        projects: list[ProjectEntry] = []
        for bullet in bullets:
            if any(token in bullet.lower() for token in ("project", "built", "developed", "platform")):
                projects.append(
                    ProjectEntry(
                        name=bullet[:80],
                        description=bullet,
                        technologies=skills[:3],
                    )
                )
        if not projects and bullets:
            projects.append(
                ProjectEntry(
                    name=f"{title} initiative",
                    description=bullets[0],
                    technologies=skills[:3],
                )
            )

        responsibilities = bullets[:6] or ["Collaborate with cross-functional teams"]
        topics = skills[:5] + [entry.title for entry in experience[:2]]
        headline = lines[0][:300] if lines else title
        summary = f"{headline}. Key skills: {', '.join(skills[:6])}."

        return ParsedResumeProfile(
            headline=headline,
            years_experience=_infer_years(raw_text),
            skills=skills,
            experience=experience[:6],
            projects=projects[:4],
            responsibilities=responsibilities,
            likely_interview_topics=_unique(topics)[:10],
            summary_text=summary[:500],
        )

    async def extract_job_description(
        self,
        raw_text: str,
        *,
        title: str,
        company_name: str | None = None,
    ) -> ParsedJobRequirements:
        lines = _lines(raw_text)
        bullets = _bullet_items(lines)

        required_skills = bullets[:8] or [
            hint.title()
            for hint in self._SKILL_HINTS
            if hint in raw_text.lower()
        ][:8]
        if not required_skills:
            required_skills = ["Communication", "Collaboration"]

        responsibilities = bullets[:8] or [
            line for line in lines if len(line) <= 160
        ][:6]
        technical_topics = [
            skill
            for skill in required_skills
            if any(
                token in skill.lower()
                for token in ("python", "java", "aws", "api", "system", "data", "cloud")
            )
        ][:8]
        if not technical_topics:
            technical_topics = required_skills[:5]

        behavioral_topics = [
            "Ownership and impact",
            "Cross-functional collaboration",
            "Communication under ambiguity",
        ]
        rubric_hints = [
            "Assess depth of relevant experience against required skills.",
            "Check alignment between past work and listed responsibilities.",
            "Evaluate clarity, structure, and role-specific judgment.",
        ]
        summary = (
            f"{title} at {company_name or 'the company'}: "
            f"requires {', '.join(required_skills[:5])}."
        )

        return ParsedJobRequirements(
            role_title=title,
            experience_level=_infer_level(raw_text),
            required_skills=required_skills,
            preferred_skills=required_skills[4:8],
            responsibilities=responsibilities,
            technical_topics=technical_topics,
            behavioral_topics=behavioral_topics,
            likely_interview_topics=_unique(required_skills + technical_topics)[:12],
            evaluation_rubric_hints=rubric_hints,
            summary_text=summary[:500],
        )


class LLMContextExtractor:
    def __init__(self, structured_provider: StructuredOutputProvider) -> None:
        self._structured = structured_provider

    async def extract_resume(self, raw_text: str, *, title: str) -> ParsedResumeProfile:
        messages = build_resume_extraction_messages(title, raw_text)
        return await self._structured.generate_structured(messages, ParsedResumeProfile)

    async def extract_job_description(
        self,
        raw_text: str,
        *,
        title: str,
        company_name: str | None = None,
    ) -> ParsedJobRequirements:
        messages = build_job_description_extraction_messages(title, raw_text, company_name)
        return await self._structured.generate_structured(messages, ParsedJobRequirements)


def _infer_years(raw_text: str) -> int | None:
    match = re.search(r"(\d+)\+?\s*years?", raw_text, re.IGNORECASE)
    if match:
        return min(int(match.group(1)), 40)
    return None


def _infer_level(raw_text: str) -> str | None:
    lowered = raw_text.lower()
    if "senior" in lowered or "staff" in lowered:
        return "senior"
    if "junior" in lowered or "entry" in lowered:
        return "junior"
    if "mid" in lowered or "intermediate" in lowered:
        return "mid"
    return None


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(value)
    return output
