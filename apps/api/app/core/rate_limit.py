"""In-process sliding-window rate limiting.

Suitable for a single-process modular monolith. If the API is ever scaled
horizontally, swap the backing store for Redis behind the same interface.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock

from fastapi import Request

from app.config import settings
from app.core.exceptions import RateLimitedError


@dataclass
class SlidingWindowLimiter:
    """Allows at most `limit` hits per `window_seconds` for each key."""

    limit: int
    window_seconds: float
    _hits: dict[str, deque[float]] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def check(self, key: str) -> bool:
        """Record a hit for `key`; return False if the limit is exceeded."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._hits.get(key)
            if bucket is None:
                bucket = deque()
                self._hits[key] = bucket
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            # Opportunistically drop empty buckets to bound memory.
            if len(self._hits) > 10_000:
                stale = [k for k, v in self._hits.items() if not v or v[-1] <= cutoff]
                for k in stale:
                    del self._hits[k]
            return True


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_dependency(name: str, limit: int, window_seconds: float):
    """Build a FastAPI dependency enforcing `limit` requests per window per IP."""
    limiter = SlidingWindowLimiter(limit=limit, window_seconds=window_seconds)

    async def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled or settings.is_test:
            return
        if not limiter.check(f"{name}:{client_ip(request)}"):
            raise RateLimitedError()

    return dependency
