from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TypeVar

from pydantic import BaseModel

from app.ai.errors import AIProviderError, AIResponseError
from app.ai.logging import log_ai_event
from app.ai.providers.base import StructuredOutputProvider, StreamingTextProvider, TextGenerationProvider
from app.ai.providers.openai._client import OpenAIClientFactory, OpenAISettings, map_openai_exception
from app.ai.retry import run_with_retry
from app.ai.types import ChatMessage, TextGenerationResult, TokenUsage
from app.ai.usage import record_token_usage

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)
PROVIDER = "openai"


def _normalize_messages(messages: list[ChatMessage] | list[dict[str, str]]) -> list[dict[str, str]]:
    if not messages:
        return []
    if isinstance(messages[0], ChatMessage):
        return [message.to_openai() for message in messages]  # type: ignore[union-attr]
    return messages  # type: ignore[return-value]


class OpenAITextGenerationProvider:
    def __init__(self, client_factory: OpenAIClientFactory, openai_settings: OpenAISettings) -> None:
        self._client_factory = client_factory
        self._settings = openai_settings

    async def generate_text(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> TextGenerationResult:
        selected_model = model or self._settings.llm_model

        async def operation() -> TextGenerationResult:
            client = self._client_factory.create()
            try:
                response = await client.chat.completions.create(
                    model=selected_model,
                    messages=[message.to_openai() for message in messages],
                    temperature=temperature,
                )
            except Exception as exc:  # noqa: BLE001
                raise map_openai_exception(exc) from exc

            choice = response.choices[0].message.content or ""
            usage = None
            if response.usage is not None:
                usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )
            return TextGenerationResult(text=choice, model=response.model, usage=usage)

        log_ai_event(logging.INFO, "Generating text", operation="generate_text", provider=PROVIDER, model=selected_model)
        result = await self._run_with_retry(operation)
        log_ai_event(
            logging.INFO,
            "Generated text",
            operation="generate_text",
            provider=PROVIDER,
            model=result.model,
            prompt_tokens=result.usage.prompt_tokens if result.usage else None,
            completion_tokens=result.usage.completion_tokens if result.usage else None,
        )
        return result

    async def _run_with_retry(self, operation: Callable[[], Awaitable[T]]) -> T:
        return await run_with_retry(
            operation,
            max_retries=self._settings.max_retries,
            backoff_seconds=self._settings.retry_backoff_seconds,
        )


class OpenAIStructuredOutputProvider:
    def __init__(self, client_factory: OpenAIClientFactory, openai_settings: OpenAISettings) -> None:
        self._client_factory = client_factory
        self._settings = openai_settings

    async def generate_structured(
        self,
        messages: list[ChatMessage] | list[dict[str, str]],
        response_model: type[T],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> T:
        selected_model = model or self._settings.structured_model
        normalized = _normalize_messages(messages)

        async def call(payload: list[dict[str, str]]) -> T:
            client = self._client_factory.create()
            try:
                response = await client.beta.chat.completions.parse(
                    model=selected_model,
                    messages=payload,
                    response_format=response_model,
                    temperature=temperature,
                )
            except Exception as exc:  # noqa: BLE001
                raise map_openai_exception(exc) from exc

            usage = None
            if response.usage is not None:
                usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )
            record_token_usage(usage)

            parsed = response.choices[0].message.parsed
            if parsed is None:
                raise AIResponseError("OpenAI structured response did not contain parsed output")
            return parsed

        async def operation() -> T:
            try:
                return await call(normalized)
            except AIResponseError:
                # One schema-repair attempt: re-ask with an explicit corrective
                # instruction before giving up.
                log_ai_event(
                    logging.WARNING,
                    "Structured output parse failed; retrying with repair instruction",
                    operation="generate_structured",
                    provider=PROVIDER,
                    model=selected_model,
                    schema=response_model.__name__,
                )
                repair_message = {
                    "role": "user",
                    "content": (
                        "Your previous response could not be parsed. Respond again with "
                        f"only a valid JSON object matching the {response_model.__name__} "
                        "schema. Do not include any other text."
                    ),
                }
                return await call([*normalized, repair_message])

        log_ai_event(
            logging.INFO,
            "Generating structured output",
            operation="generate_structured",
            provider=PROVIDER,
            model=selected_model,
            schema=response_model.__name__,
        )
        return await run_with_retry(
            operation,
            max_retries=self._settings.max_retries,
            backoff_seconds=self._settings.retry_backoff_seconds,
        )


class OpenAIStreamingTextProvider:
    def __init__(self, client_factory: OpenAIClientFactory, openai_settings: OpenAISettings) -> None:
        self._client_factory = client_factory
        self._settings = openai_settings

    async def stream_text(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        selected_model = model or self._settings.streaming_model
        log_ai_event(
            logging.INFO,
            "Streaming text",
            operation="stream_text",
            provider=PROVIDER,
            model=selected_model,
        )

        client = self._client_factory.create()
        try:
            stream = await client.chat.completions.create(
                model=selected_model,
                messages=[message.to_openai() for message in messages],
                temperature=temperature,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except AIProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise map_openai_exception(exc) from exc
