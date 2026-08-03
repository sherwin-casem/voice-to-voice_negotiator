from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.base import StructuredOutputProvider
from app.ai.providers.factory import get_ai_providers
from app.api.deps import get_async_session
from app.config import settings
from app.modules.interview.interviewer_agent import InterviewerAgent, MockInterviewerLLMProvider
from app.modules.interview.orchestrator import InterviewOrchestrator
from app.modules.interview.repository import InterviewRepository
from app.modules.context.deps import get_context_preparation_service
from app.modules.context.service import ContextPreparationService

__all__ = [
    "get_user_id",
    "get_interview_orchestrator",
    "get_interview_repository",
    "get_interviewer_agent",
]


def get_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> UUID:
    """Dev-only user scoping until authentication is implemented."""
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="X-User-Id header is required")
    try:
        return UUID(x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="X-User-Id must be a valid UUID") from exc


def get_interviewer_agent(
    structured_provider: StructuredOutputProvider | None = None,
) -> InterviewerAgent:
    if structured_provider is not None:
        return InterviewerAgent(structured_provider)

    if settings.ai_provider == "mock":
        return InterviewerAgent(MockInterviewerLLMProvider())

    return InterviewerAgent(get_ai_providers().structured)


async def get_interview_orchestrator(
    session: AsyncSession = Depends(get_async_session),
    context_preparation: ContextPreparationService = Depends(get_context_preparation_service),
) -> InterviewOrchestrator:
    repository = InterviewRepository(session)
    interviewer = get_interviewer_agent()
    return InterviewOrchestrator(repository, interviewer, context_preparation)


async def get_interview_repository(
    session: AsyncSession = Depends(get_async_session),
) -> InterviewRepository:
    return InterviewRepository(session)
