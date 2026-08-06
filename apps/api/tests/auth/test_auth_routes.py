import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.db.enums import InterviewSessionStatus, InterviewType
from app.db.models.interview import InterviewSession
from app.modules.auth.deps import get_user_id
from app.modules.interview.deps import get_interview_repository
from app.modules.interview.repository import InterviewRepository


async def test_protected_route_rejects_missing_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/sessions")

    assert response.status_code == 401


async def test_protected_route_accepts_authenticated_user(client: AsyncClient) -> None:
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    interview_session = InterviewSession(
        id=session_id,
        user_id=user_id,
        interview_type=InterviewType.BEHAVIORAL,
        status=InterviewSessionStatus.COMPLETED,
        title="Owned session",
        config_snapshot={"target_role": "Engineer"},
        question_count=3,
    )

    mock_repo = AsyncMock(spec=InterviewRepository)
    mock_repo.list_sessions_for_user.return_value = [interview_session]
    mock_repo.get_latest_overall_scores.return_value = {session_id: 82.0}

    async def override_user_id() -> uuid.UUID:
        return user_id

    async def override_repository() -> AsyncMock:
        return mock_repo

    client._transport.app.dependency_overrides[get_user_id] = override_user_id
    client._transport.app.dependency_overrides[get_interview_repository] = override_repository

    try:
        response = await client.get("/api/v1/sessions", headers={"Authorization": "Bearer token"})
        assert response.status_code == 200
        body = response.json()
        assert body["error"] is None
        items = body["data"]["items"]
        assert len(items) == 1
        assert items[0]["id"] == str(session_id)
        assert items[0]["overall_score"] == 82.0
        mock_repo.list_sessions_for_user.assert_awaited_once_with(user_id, limit=20, offset=0)
    finally:
        client._transport.app.dependency_overrides.clear()


async def test_auth_me_requires_bearer(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
