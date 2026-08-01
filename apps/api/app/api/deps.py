from collections.abc import AsyncGenerator, Generator
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.session import get_async_session, get_session
from app.modules.interview.interviewer_agent import InterviewerAgent, MockInterviewerLLMProvider
from app.modules.interview.orchestrator import InterviewOrchestrator
from app.modules.interview.repository import InterviewRepository

__all__ = [
    "get_session",
    "get_async_session",
    "get_user_id",
    "get_interview_orchestrator",
    "get_interview_repository",
    "DbSession",
    "AsyncDbSession",
]

DbSession = Generator[Session, None, None]
AsyncDbSession = AsyncGenerator[AsyncSession, None]


def get_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> UUID:
    """Dev-only user scoping until authentication is implemented."""
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="X-User-Id header is required")
    try:
        return UUID(x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="X-User-Id must be a valid UUID") from exc


async def get_interview_orchestrator(
    session: AsyncSession = Depends(get_async_session),
) -> InterviewOrchestrator:
    repository = InterviewRepository(session)
    interviewer = InterviewerAgent(MockInterviewerLLMProvider())
    return InterviewOrchestrator(repository, interviewer)


async def get_interview_repository(
    session: AsyncSession = Depends(get_async_session),
) -> InterviewRepository:
    return InterviewRepository(session)
