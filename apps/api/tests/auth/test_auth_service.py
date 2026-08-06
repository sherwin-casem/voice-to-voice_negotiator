import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest

from app.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.db.models.user import RefreshToken, User, UserProfile
from app.modules.auth.service import (
    ACCESS_TOKEN_TYPE,
    AuthRepository,
    AuthService,
    create_access_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    hashed = hash_password("secure-password")
    assert hashed != "secure-password"
    assert verify_password("secure-password", hashed)
    assert not verify_password("wrong-password", hashed)


def test_verify_password_rejects_dev_hash() -> None:
    assert not verify_password("dev", "dev")


def test_create_and_decode_access_token() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "user@example.com")
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["email"] == "user@example.com"
    assert payload["type"] == ACCESS_TOKEN_TYPE


def test_decode_access_token_rejects_invalid_token() -> None:
    with pytest.raises(UnauthorizedError):
        decode_access_token("not-a-token")


def test_decode_access_token_rejects_wrong_type() -> None:
    payload = {
        "sub": str(uuid.uuid4()),
        "email": "user@example.com",
        "type": "refresh",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    with pytest.raises(UnauthorizedError):
        decode_access_token(token)


def _user(email: str = "user@example.com") -> User:
    user = User(id=uuid.uuid4(), email=email, password_hash=hash_password("password123"))
    user.profile = UserProfile(user_id=user.id)
    user.is_active = True
    return user


@pytest.fixture
def auth_repository() -> AsyncMock:
    return AsyncMock(spec=AuthRepository)


@pytest.fixture
def auth_service(auth_repository: AsyncMock) -> AuthService:
    return AuthService(auth_repository)


async def test_register_creates_user_and_tokens(auth_service: AuthService, auth_repository: AsyncMock) -> None:
    auth_repository.get_user_by_email.return_value = None
    user = _user()
    auth_repository.create_user.return_value = user
    auth_repository.store_refresh_token.return_value = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash="hash",
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )

    registered_user, access_token, refresh_token = await auth_service.register(
        "user@example.com",
        "password123",
    )

    assert registered_user is user
    assert access_token
    assert refresh_token
    auth_repository.create_user.assert_awaited_once()
    auth_repository.store_refresh_token.assert_awaited_once()


async def test_register_duplicate_email_raises(auth_service: AuthService, auth_repository: AsyncMock) -> None:
    auth_repository.get_user_by_email.return_value = _user()

    with pytest.raises(ConflictError):
        await auth_service.register("user@example.com", "password123")


async def test_login_success(auth_service: AuthService, auth_repository: AsyncMock) -> None:
    user = _user()
    auth_repository.get_user_by_email.return_value = user

    logged_in_user, access_token, refresh_token = await auth_service.login(
        "user@example.com",
        "password123",
    )

    assert logged_in_user is user
    assert access_token
    assert refresh_token


async def test_login_wrong_password_raises(auth_service: AuthService, auth_repository: AsyncMock) -> None:
    auth_repository.get_user_by_email.return_value = _user()

    with pytest.raises(UnauthorizedError):
        await auth_service.login("user@example.com", "wrong-password")


async def test_refresh_rotates_token(auth_service: AuthService, auth_repository: AsyncMock) -> None:
    user = _user()
    refresh_token = "refresh-token-value"
    record = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    auth_repository.get_refresh_token.return_value = record
    auth_repository.get_user_by_id.return_value = user

    refreshed_user, access_token, new_refresh = await auth_service.refresh(refresh_token)

    assert refreshed_user is user
    assert access_token
    assert new_refresh
    auth_repository.revoke_refresh_token.assert_awaited_once_with(refresh_token)
    auth_repository.store_refresh_token.assert_awaited_once()


async def test_refresh_rejects_revoked_token(auth_service: AuthService, auth_repository: AsyncMock) -> None:
    auth_repository.get_refresh_token.return_value = None

    with pytest.raises(UnauthorizedError):
        await auth_service.refresh("missing-token")


async def test_refresh_rejects_expired_token(auth_service: AuthService, auth_repository: AsyncMock) -> None:
    record = RefreshToken(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        token_hash=hash_refresh_token("expired"),
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    auth_repository.get_refresh_token.return_value = record

    with pytest.raises(UnauthorizedError):
        await auth_service.refresh("expired")


async def test_logout_revokes_refresh_token(auth_service: AuthService, auth_repository: AsyncMock) -> None:
    await auth_service.logout("refresh-token")
    auth_repository.revoke_refresh_token.assert_awaited_once_with("refresh-token")
