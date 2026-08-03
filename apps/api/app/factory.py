import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.rest.router import api_v1_router
from app.api.ws.interview import router as interview_ws_router
from app.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware
from app.core.security import SecurityHeadersMiddleware
from app.core.startup import validate_settings
from app.db.session import async_engine, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    validate_settings(settings)
    logger.info(
        "Starting API",
        extra={"component": "startup", "app_env": settings.app_env},
    )
    yield
    await async_engine.dispose()
    engine.dispose()
    logger.info("Stopped API", extra={"component": "shutdown"})


def create_app() -> FastAPI:
    docs_url = "/docs" if settings.is_development else None
    redoc_url = "/redoc" if settings.is_development else None

    app = FastAPI(
        title="Voice-to-Voice Interview Negotiator API",
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    register_error_handlers(app)
    app.include_router(api_v1_router)
    app.include_router(interview_ws_router, prefix="/api/v1")

    return app
