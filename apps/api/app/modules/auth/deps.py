from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_async_session
from app.config import settings
from app.core.exceptions import UnauthorizedError
from app.db.models.user import User
from app.modules.auth.service import AuthRepository, AuthService, decode_access_token


async def get_auth_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    return AuthService(AuthRepository(session))


async def _resolve_bearer_user(authorization: str | None, session: AsyncSession) -> User | None:
    """Resolve the Bearer token to an active user, or None if no token present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None

    payload = decode_access_token(token)
    user_id = UUID(payload["sub"])
    user = await AuthRepository(session).get_user_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    user = await _resolve_bearer_user(authorization, session)
    if user is None:
        raise UnauthorizedError("Authentication required")
    return user


async def get_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    session: AsyncSession = Depends(get_async_session),
) -> UUID:
    user = await _resolve_bearer_user(authorization, session)
    if user is not None:
        return user.id

    if settings.allow_dev_user_header and settings.is_development and x_user_id:
        try:
            return UUID(x_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="X-User-Id must be a valid UUID") from exc

    raise HTTPException(status_code=401, detail="Authentication required")
