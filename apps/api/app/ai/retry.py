import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.ai.errors import AIProviderError

T = TypeVar("T")
logger = logging.getLogger(__name__)


async def run_with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    max_retries: int,
    backoff_seconds: float,
    on_retry: Callable[[AIProviderError, int], None] | None = None,
) -> T:
    attempt = 0
    while True:
        try:
            return await operation()
        except AIProviderError as exc:
            if not exc.retryable or attempt >= max_retries:
                raise
            attempt += 1
            if on_retry is not None:
                on_retry(exc, attempt)
            delay = backoff_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Retrying AI operation after failure",
                extra={
                    "component": "ai",
                    "error_code": exc.code,
                    "attempt": attempt,
                    "max_retries": max_retries,
                    "delay_seconds": delay,
                },
            )
            await asyncio.sleep(delay)
