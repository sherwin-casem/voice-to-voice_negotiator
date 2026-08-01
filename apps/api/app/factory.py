import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.rest.router import api_v1_router
from app.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware
from app.db.session import async_engine, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info(
        "Starting API",
        extra={"component": "startup", "app_env": settings.app_env},
    )
    yield
    await async_engine.dispose()
    engine.dispose()
    logger.info("Stopped API", extra={"component": "shutdown"})


def create_app() -> FastAPI:
    app = FastAPI(
        title="Voice-to-Voice Interview Negotiator API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

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

    return app
