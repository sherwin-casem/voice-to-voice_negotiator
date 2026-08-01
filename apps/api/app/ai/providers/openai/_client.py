from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from openai import AsyncOpenAI

from app.ai.errors import AIAuthenticationError, AIConfigurationError, AIProviderError
from app.config import Settings, settings


def map_openai_exception(exc: Exception) -> AIProviderError:
    from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError
    from openai import APIStatusError

    if isinstance(exc, AuthenticationError):
        return AIAuthenticationError("OpenAI authentication failed")
    if isinstance(exc, RateLimitError):
        return AIProviderError("AI_RATE_LIMIT", "OpenAI rate limit exceeded", retryable=True, status_code=429)
    if isinstance(exc, APITimeoutError):
        return AIProviderError("AI_TIMEOUT", "OpenAI request timed out", retryable=True)
    if isinstance(exc, APIConnectionError):
        return AIProviderError("AI_CONNECTION_ERROR", "OpenAI connection failed", retryable=True)
    if isinstance(exc, APIStatusError):
        retryable = exc.status_code >= 500
        return AIProviderError(
            "AI_UNAVAILABLE" if retryable else "AI_RESPONSE_ERROR",
            f"OpenAI API error ({exc.status_code})",
            retryable=retryable,
            status_code=exc.status_code,
        )
    return AIProviderError("AI_RESPONSE_ERROR", str(exc), retryable=False)


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str
    organization: str | None
    base_url: str | None
    timeout_seconds: float
    max_retries: int
    retry_backoff_seconds: float
    llm_model: str
    structured_model: str
    streaming_model: str
    stt_model: str
    tts_model: str
    tts_voice: str

    @classmethod
    def from_app_settings(cls, app_settings: Settings) -> OpenAISettings:
        if not app_settings.openai_api_key:
            raise AIConfigurationError("OPENAI_API_KEY is not configured")
        return cls(
            api_key=app_settings.openai_api_key,
            organization=app_settings.openai_organization,
            base_url=app_settings.openai_base_url,
            timeout_seconds=app_settings.ai_request_timeout_seconds,
            max_retries=app_settings.ai_max_retries,
            retry_backoff_seconds=app_settings.ai_retry_backoff_seconds,
            llm_model=app_settings.openai_llm_model,
            structured_model=app_settings.openai_structured_model,
            streaming_model=app_settings.openai_streaming_model,
            stt_model=app_settings.openai_stt_model,
            tts_model=app_settings.openai_tts_model,
            tts_voice=app_settings.openai_tts_voice,
        )


class OpenAIClientFactory:
    def __init__(self, openai_settings: OpenAISettings) -> None:
        self._settings = openai_settings

    def create(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=self._settings.api_key,
            organization=self._settings.organization,
            base_url=self._settings.base_url,
            timeout=self._settings.timeout_seconds,
            max_retries=0,
        )


ProviderName = Literal["mock", "openai"]


@lru_cache
def get_openai_settings() -> OpenAISettings:
    return OpenAISettings.from_app_settings(settings)


def get_openai_client_factory() -> OpenAIClientFactory:
    return OpenAIClientFactory(get_openai_settings())
