import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.db.models.user import RefreshToken, User, UserProfile

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
WS_TICKET_TOKEN_TYPE = "ws_ticket"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash == "dev":
        return False
    return pwd_context.verify(password, password_hash)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: UUID, email: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_ttl_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": ACCESS_TOKEN_TYPE,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired access token") from exc
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise UnauthorizedError("Invalid token type")
    return payload


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_ws_ticket(user_id: UUID, session_id: UUID) -> str:
    """Short-lived, session-bound token safe to place in a WebSocket URL."""
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.ws_ticket_ttl_seconds)
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "type": WS_TICKET_TOKEN_TYPE,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_ws_ticket(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired connection ticket") from exc
    if payload.get("type") != WS_TICKET_TOKEN_TYPE:
        raise UnauthorizedError("Invalid token type")
    return payload


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email.lower()).options(selectinload(User.profile))
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id).options(selectinload(User.profile))
        )
        return result.scalar_one_or_none()

    async def create_user(self, email: str, password_hash: str) -> User:
        user = User(email=email.lower(), password_hash=password_hash)
        self._session.add(user)
        await self._session.flush()
        profile = UserProfile(user_id=user.id)
        self._session.add(profile)
        await self._session.flush()
        user.profile = profile
        return user

    async def store_refresh_token(self, user_id: UUID, token: str) -> RefreshToken:
        expires_at = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days)
        record = RefreshToken(
            id=uuid4(),
            user_id=user_id,
            token_hash=hash_refresh_token(token),
            expires_at=expires_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_refresh_token(self, token: str) -> RefreshToken | None:
        token_hash = hash_refresh_token(token)
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_refresh_token_any(self, token: str) -> RefreshToken | None:
        """Look up a refresh token regardless of revocation (reuse detection)."""
        token_hash = hash_refresh_token(token)
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token: str) -> None:
        record = await self.get_refresh_token(token)
        if record is None:
            return
        record.revoked_at = datetime.now(UTC)
        await self._session.flush()

    async def revoke_refresh_token_atomic(self, token: str) -> bool:
        """Revoke with a guarded UPDATE; returns False if it was already revoked.

        Two concurrent refresh requests with the same token race on this
        update — exactly one wins, the other is treated as token reuse.
        """
        token_hash = hash_refresh_token(token)
        result = await self._session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.flush()
        return result.rowcount > 0

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.flush()

    async def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(UTC)
        await self._session.flush()


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def _user_for_response(self, user_id: UUID) -> User:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")
        return user

    async def register(self, email: str, password: str) -> tuple[User, str, str]:
        existing = await self._repository.get_user_by_email(email)
        if existing is not None:
            raise ConflictError("An account with this email already exists")

        try:
            user = await self._repository.create_user(email, hash_password(password))
        except IntegrityError as exc:
            # Concurrent registration with the same email lost the unique-index
            # race; surface it the same way as the pre-check.
            raise ConflictError("An account with this email already exists") from exc
        access_token = create_access_token(user.id, user.email)
        refresh_token = generate_refresh_token()
        await self._repository.store_refresh_token(user.id, refresh_token)
        await self._repository.update_last_login(user)
        return await self._user_for_response(user.id), access_token, refresh_token

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        user = await self._repository.get_user_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            logger.info(
                "Login failed: invalid credentials",
                extra={"component": "auth", "auth_event": "login_failed"},
            )
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            logger.info(
                "Login failed: inactive account",
                extra={
                    "component": "auth",
                    "auth_event": "login_inactive",
                    "user_id": str(user.id),
                },
            )
            raise UnauthorizedError("Account is inactive")

        access_token = create_access_token(user.id, user.email)
        refresh_token = generate_refresh_token()
        await self._repository.store_refresh_token(user.id, refresh_token)
        await self._repository.update_last_login(user)
        logger.info(
            "Login succeeded",
            extra={"component": "auth", "auth_event": "login_success", "user_id": str(user.id)},
        )
        return await self._user_for_response(user.id), access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[User, str, str]:
        record = await self._repository.get_refresh_token_any(refresh_token)
        if record is None:
            raise UnauthorizedError("Invalid refresh token")

        if record.revoked_at is not None:
            # Reuse of a rotated token: assume the token family is compromised
            # and revoke every active session for the user.
            logger.warning(
                "Refresh token reuse detected; revoking all sessions",
                extra={
                    "component": "auth",
                    "auth_event": "refresh_reuse",
                    "user_id": str(record.user_id),
                },
            )
            await self._repository.revoke_all_for_user(record.user_id)
            raise UnauthorizedError("Invalid refresh token")

        if record.expires_at <= datetime.now(UTC):
            raise UnauthorizedError("Refresh token expired")

        user = await self._repository.get_user_by_id(record.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Account is inactive")

        rotated = await self._repository.revoke_refresh_token_atomic(refresh_token)
        if not rotated:
            # A concurrent request rotated this token first — treat as reuse.
            logger.warning(
                "Concurrent refresh rotation detected; revoking all sessions",
                extra={
                    "component": "auth",
                    "auth_event": "refresh_reuse",
                    "user_id": str(record.user_id),
                },
            )
            await self._repository.revoke_all_for_user(record.user_id)
            raise UnauthorizedError("Invalid refresh token")

        access_token = create_access_token(user.id, user.email)
        new_refresh_token = generate_refresh_token()
        await self._repository.store_refresh_token(user.id, new_refresh_token)
        return user, access_token, new_refresh_token

    async def logout(self, refresh_token: str | None) -> None:
        if refresh_token:
            await self._repository.revoke_refresh_token(refresh_token)

    async def get_user_profile(self, user_id: UUID) -> User:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")
        return user
