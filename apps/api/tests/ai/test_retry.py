import pytest

from app.ai.errors import AIProviderError
from app.ai.retry import run_with_retry


@pytest.mark.asyncio
async def test_run_with_retry_retries_retryable_errors() -> None:
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise AIProviderError("AI_RATE_LIMIT", "rate limited", retryable=True)
        return "ok"

    result = await run_with_retry(operation, max_retries=3, backoff_seconds=0)
    assert result == "ok"
    assert attempts == 3


@pytest.mark.asyncio
async def test_run_with_retry_does_not_retry_non_retryable_errors() -> None:
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        raise AIProviderError("AI_RESPONSE_ERROR", "bad request", retryable=False)

    with pytest.raises(AIProviderError):
        await run_with_retry(operation, max_retries=3, backoff_seconds=0)
    assert attempts == 1
