from collections.abc import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.session import get_async_session, get_session

__all__ = ["get_session", "get_async_session", "DbSession", "AsyncDbSession"]

DbSession = Generator[Session, None, None]
AsyncDbSession = AsyncGenerator[AsyncSession, None]
