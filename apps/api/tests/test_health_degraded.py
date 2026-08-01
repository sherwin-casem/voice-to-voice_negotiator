from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session
from app.factory import create_app


@pytest.fixture
async def degraded_client() -> AsyncGenerator[AsyncClient, None]:
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(side_effect=RuntimeError("connection refused"))
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()

    app = create_app()

    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_async_session] = override_get_async_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client

    app.dependency_overrides.clear()


async def test_health_check_reports_degraded_when_database_unavailable(
    degraded_client: AsyncClient,
) -> None:
    response = await degraded_client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "degraded"
    assert body["data"]["database"] == "error"
