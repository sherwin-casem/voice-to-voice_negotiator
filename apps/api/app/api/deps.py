from collections.abc import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.session import get_async_session as _get_async_session
from app.db.session import get_session as _get_session

__all__ = ["get_session", "get_async_session", "DbSession", "AsyncDbSession"]

DbSession = Generator[Session, None, None]
AsyncDbSession = AsyncGenerator[AsyncSession, None]


def get_session() -> DbSession:
    yield from _get_session()


async def get_async_session() -> AsyncDbSession:
    async for session in _get_async_session():
        yield session
