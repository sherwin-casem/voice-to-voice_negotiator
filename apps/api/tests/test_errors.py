from httpx import ASGITransport, AsyncClient

from app.core.exceptions import AppError, NotFoundError
from app.factory import create_app


async def test_not_found_error_returns_structured_envelope() -> None:
    app = create_app()

    @app.get("/api/v1/test-not-found")
    async def trigger_not_found() -> None:
        raise NotFoundError("Session not found")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        response = await http_client.get("/api/v1/test-not-found")

    assert response.status_code == 404
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"] == "Session not found"
    assert body["error"]["request_id"] is not None


async def test_app_error_includes_request_id() -> None:
    app = create_app()

    @app.get("/api/v1/test-app-error")
    async def trigger_app_error() -> None:
        raise AppError("TEST_ERROR", "Something went wrong", status_code=418)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        response = await http_client.get("/api/v1/test-app-error")

    assert response.status_code == 418
    body = response.json()
    assert body["error"]["code"] == "TEST_ERROR"
    assert body["error"]["request_id"] is not None
