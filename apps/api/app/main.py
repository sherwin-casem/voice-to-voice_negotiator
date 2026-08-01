from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.rest.health import router as health_router
from app.config import settings

app = FastAPI(
    title="Voice-to-Voice Interview Negotiator API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
