"""Optional feature routers (voice WebSocket, dev utilities).

Interview REST routes are registered in app.api.rest.router.
"""

from fastapi import APIRouter

from app.api.rest.dev import dev_router
from app.api.ws.interview import router as interview_ws_router


def register_feature_routes(router: APIRouter) -> None:
    router.include_router(dev_router)
    router.include_router(interview_ws_router)
