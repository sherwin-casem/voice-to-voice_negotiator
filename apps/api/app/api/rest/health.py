import logging

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session
from app.config import settings
from app.db.health import check_database
from app.schemas.common import ApiResponse, HealthData

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=ApiResponse[HealthData])
async def liveness_check() -> ApiResponse[HealthData]:
    """Process-level liveness: no dependencies checked, never degrades."""
    return ApiResponse(
        data=HealthData(
            status="ok",
            database="not_checked",
            environment=settings.app_env,
        )
    )


async def _readiness(
    response: Response,
    session: AsyncSession,
) -> ApiResponse[HealthData]:
    database_status = "ok"
    try:
        await check_database(session)
    except Exception:
        logger.exception("Database health check failed", extra={"component": "health"})
        database_status = "error"

    overall_status = "ok" if database_status == "ok" else "degraded"
    if overall_status == "degraded":
        response.status_code = 503

    return ApiResponse(
        data=HealthData(
            status=overall_status,
            database=database_status,
            environment=settings.app_env,
        )
    )


@router.get("/health/ready", response_model=ApiResponse[HealthData])
async def readiness_check(
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> ApiResponse[HealthData]:
    """Readiness: verifies the database is reachable."""
    return await _readiness(response, session)


@router.get("/health", response_model=ApiResponse[HealthData])
async def health_check(
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> ApiResponse[HealthData]:
    """Legacy combined health endpoint (same semantics as /health/ready)."""
    return await _readiness(response, session)
