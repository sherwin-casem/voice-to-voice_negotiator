import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.core.exceptions import AppError
from app.core.middleware import get_request_id
from app.schemas.common import ApiError, ApiResponse

logger = logging.getLogger(__name__)


def _error_body(code: str, message: str, request_id: str | None) -> dict[str, object]:
    return ApiResponse(
        data=None,
        error=ApiError(code=code, message=message, request_id=request_id),
    ).model_dump()


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        request_id = get_request_id()
        logger.warning(
            "Application error: %s",
            exc.message,
            extra={"component": "error_handler", "error_code": exc.code},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, request_id),
        )

    @app.exception_handler(HTTPException)
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(_request: Request, exc: HTTPException) -> JSONResponse:
        request_id = get_request_id()
        detail = exc.detail
        if isinstance(detail, str):
            message = detail
        elif isinstance(detail, dict):
            message = str(detail.get("message", detail))
        else:
            message = "Request failed"

        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(f"HTTP_{exc.status_code}", message, request_id),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        request_id = get_request_id()
        return JSONResponse(
            status_code=422,
            content=_error_body("VALIDATION_ERROR", "Request validation failed", request_id),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        request_id = get_request_id()
        logger.exception(
            "Unhandled exception",
            extra={"component": "error_handler"},
        )
        message = str(exc) if settings.debug else "An unexpected error occurred"
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", message, request_id),
        )
