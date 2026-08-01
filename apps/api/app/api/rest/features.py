"""Optional feature routers (interviews, voice, dev).

Not registered by the application factory until those features are product-ready.
"""

from fastapi import APIRouter

from app.api.rest.dev import dev_router
from app.api.rest.sessions import context_router, router as sessions_router
from app.api.ws.interview import router as interview_ws_router


def register_feature_routes(router: APIRouter) -> None:
    router.include_router(sessions_router)
    router.include_router(context_router)
    router.include_router(dev_router)
    router.include_router(interview_ws_router)
