from fastapi import APIRouter

from app.api.rest.health import router as health_router
from app.api.rest.sessions import context_router, router as sessions_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(context_router)
