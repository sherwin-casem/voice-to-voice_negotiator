"""Database connectivity helpers."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_database(session: AsyncSession) -> bool:
    """Return True when the database accepts a simple query."""
    await session.execute(text("SELECT 1"))
    return True
