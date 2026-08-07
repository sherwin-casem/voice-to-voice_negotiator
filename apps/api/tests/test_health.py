from httpx import AsyncClient


async def test_health_check_returns_ok_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] == "ok"


async def test_liveness_never_touches_database(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] == "not_checked"


async def test_readiness_checks_database(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] == "ok"


async def test_health_check_includes_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]


async def test_health_check_propagates_request_id(client: AsyncClient) -> None:
    request_id = "test-request-id-12345"
    response = await client.get(
        "/api/v1/health",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
