from pathlib import Path

from app.ai.schemas.context import ParsedJobRequirements, ParsedResumeProfile

PROMPT_VERSION = "1.0"
_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _load(name: str) -> str:
    return (_TEMPLATES_DIR / name).read_text(encoding="utf-8")


def build_resume_extraction_messages(title: str, raw_text: str) -> list[dict[str, str]]:
    system = _load("resume_system.txt")
    user = _load("resume_user.txt").format(title=title, raw_text=raw_text[:12000])
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_job_description_extraction_messages(
    title: str,
    raw_text: str,
    company_name: str | None,
) -> list[dict[str, str]]:
    system = _load("job_description_system.txt")
    user = _load("job_description_user.txt").format(
        title=title,
        company_name=company_name or "Not specified",
        raw_text=raw_text[:12000],
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


__all__ = [
    "PROMPT_VERSION",
    "ParsedJobRequirements",
    "ParsedResumeProfile",
    "build_job_description_extraction_messages",
    "build_resume_extraction_messages",
]
