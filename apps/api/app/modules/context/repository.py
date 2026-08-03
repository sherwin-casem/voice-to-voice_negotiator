import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.enums import DocumentParseStatus
from app.db.models.context import JobDescription, Resume


class ContextRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_resume(self, resume_id: UUID, user_id: UUID) -> Resume:
        result = await self._session.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        resume = result.scalar_one_or_none()
        if resume is None:
            raise NotFoundError("Resume not found")
        return resume

    async def get_job_description(self, job_description_id: UUID, user_id: UUID) -> JobDescription:
        result = await self._session.execute(
            select(JobDescription).where(
                JobDescription.id == job_description_id,
                JobDescription.user_id == user_id,
            )
        )
        job_description = result.scalar_one_or_none()
        if job_description is None:
            raise NotFoundError("Job description not found")
        return job_description

    async def save_resume_preparation(
        self,
        resume: Resume,
        *,
        parsed_profile: dict,
        summary_text: str,
        parse_status: DocumentParseStatus,
        source_filename: str | None = None,
        mime_type: str | None = None,
    ) -> Resume:
        resume.parsed_profile = parsed_profile
        resume.summary_text = summary_text
        resume.parse_status = parse_status
        if source_filename is not None:
            resume.source_filename = source_filename
        if mime_type is not None:
            resume.mime_type = mime_type
        await self._session.flush()
        return resume

    async def save_job_description_preparation(
        self,
        job_description: JobDescription,
        *,
        parsed_requirements: dict,
        summary_text: str,
        parse_status: DocumentParseStatus,
        source_filename: str | None = None,
        mime_type: str | None = None,
    ) -> JobDescription:
        job_description.parsed_requirements = parsed_requirements
        job_description.summary_text = summary_text
        job_description.parse_status = parse_status
        if source_filename is not None:
            job_description.source_filename = source_filename
        if mime_type is not None:
            job_description.mime_type = mime_type
        await self._session.flush()
        return job_description


_SECTION_PATTERN = re.compile(
    r"^\s*(skills|experience|employment|work history|projects|responsibilities|"
    r"technical skills|core competencies)\s*:?\s*$",
    re.IGNORECASE,
)


def _lines(raw_text: str) -> list[str]:
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def _bullet_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for line in lines:
        if line.startswith(("-", "•", "*")):
            items.append(line.lstrip("-•* ").strip())
        elif re.match(r"^\d+[.)]\s", line):
            items.append(re.sub(r"^\d+[.)]\s*", "", line).strip())
    return items
