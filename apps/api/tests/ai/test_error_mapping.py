from unittest.mock import MagicMock

from openai import APIConnectionError, AuthenticationError, RateLimitError

from app.ai.errors import AIAuthenticationError, AIProviderError
from app.ai.providers.openai._client import map_openai_exception


def _response() -> MagicMock:
    response = MagicMock()
    response.request = MagicMock()
    return response


def test_map_openai_exception_authentication() -> None:
    mapped = map_openai_exception(
        AuthenticationError(message="bad key", response=_response(), body=None),
    )
    assert isinstance(mapped, AIAuthenticationError)
    assert mapped.retryable is False


def test_map_openai_exception_rate_limit() -> None:
    mapped = map_openai_exception(
        RateLimitError(message="slow down", response=_response(), body=None),
    )
    assert isinstance(mapped, AIProviderError)
    assert mapped.retryable is True
    assert mapped.code == "AI_RATE_LIMIT"


def test_map_openai_exception_connection() -> None:
    mapped = map_openai_exception(APIConnectionError(request=MagicMock()))
    assert mapped.retryable is True
    assert mapped.code == "AI_CONNECTION_ERROR"
