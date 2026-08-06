import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.db.models.user import RefreshToken, User, UserProfile

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


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

    async def revoke_refresh_token(self, token: str) -> None:
        record = await self.get_refresh_token(token)
        if record is None:
            return
        record.revoked_at = datetime.now(UTC)
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

        user = await self._repository.create_user(email, hash_password(password))
        access_token = create_access_token(user.id, user.email)
        refresh_token = generate_refresh_token()
        await self._repository.store_refresh_token(user.id, refresh_token)
        await self._repository.update_last_login(user)
        return await self._user_for_response(user.id), access_token, refresh_token

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        user = await self._repository.get_user_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is inactive")

        access_token = create_access_token(user.id, user.email)
        refresh_token = generate_refresh_token()
        await self._repository.store_refresh_token(user.id, refresh_token)
        await self._repository.update_last_login(user)
        return await self._user_for_response(user.id), access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[User, str, str]:
        record = await self._repository.get_refresh_token(refresh_token)
        if record is None:
            raise UnauthorizedError("Invalid refresh token")
        if record.expires_at <= datetime.now(UTC):
            raise UnauthorizedError("Refresh token expired")

        user = await self._repository.get_user_by_id(record.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Account is inactive")

        await self._repository.revoke_refresh_token(refresh_token)
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
