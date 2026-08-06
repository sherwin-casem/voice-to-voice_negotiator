from fastapi import APIRouter

from app.api.rest.auth import router as auth_router
from app.api.rest.context import router as context_router
from app.api.rest.dev import dev_router
from app.api.rest.health import router as health_router
from app.api.rest.progress import router as progress_router
from app.api.rest.sessions import router as sessions_router
from app.config import settings

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(context_router)
api_v1_router.include_router(progress_router)
if settings.is_development:
    api_v1_router.include_router(dev_router)
