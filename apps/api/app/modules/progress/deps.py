from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session
from app.modules.progress.repository import ProgressRepository
from app.modules.progress.service import ProgressAnalysisService

__all__ = ["get_progress_repository", "get_progress_analysis_service"]


async def get_progress_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ProgressRepository:
    return ProgressRepository(session)


async def get_progress_analysis_service(
    repository: ProgressRepository = Depends(get_progress_repository),
) -> ProgressAnalysisService:
    return ProgressAnalysisService(repository)
