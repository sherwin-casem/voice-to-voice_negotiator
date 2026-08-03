from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.factory import get_ai_providers
from app.api.deps import get_async_session
from app.config import settings
from app.modules.context.extractor import HeuristicContextExtractor, LLMContextExtractor
from app.modules.context.repository import ContextRepository
from app.modules.context.selector import ContextSelector
from app.modules.context.service import ContextPreparationService

__all__ = ["get_context_preparation_service", "get_context_repository"]


async def get_context_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ContextRepository:
    return ContextRepository(session)


async def get_context_preparation_service(
    repository: ContextRepository = Depends(get_context_repository),
) -> ContextPreparationService:
    if settings.ai_provider == "mock":
        extractor = HeuristicContextExtractor()
    else:
        extractor = LLMContextExtractor(get_ai_providers().structured)
    return ContextPreparationService(repository, extractor, ContextSelector())
