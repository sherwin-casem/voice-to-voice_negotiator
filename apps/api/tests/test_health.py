from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_health_check_returns_ok_envelope() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"] == {"status": "ok"}
