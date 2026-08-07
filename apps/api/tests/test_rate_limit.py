from app.core.rate_limit import SlidingWindowLimiter


def test_limiter_allows_up_to_limit() -> None:
    limiter = SlidingWindowLimiter(limit=3, window_seconds=60.0)

    assert limiter.check("key")
    assert limiter.check("key")
    assert limiter.check("key")
    assert not limiter.check("key")


def test_limiter_isolates_keys() -> None:
    limiter = SlidingWindowLimiter(limit=1, window_seconds=60.0)

    assert limiter.check("a")
    assert not limiter.check("a")
    assert limiter.check("b")


def test_limiter_window_expiry() -> None:
    limiter = SlidingWindowLimiter(limit=1, window_seconds=0.0)

    assert limiter.check("key")
    # With a zero-length window every prior hit is already expired.
    assert limiter.check("key")
