from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, TypeVar

from pydantic import BaseModel

from app.ai.providers.base import (
    SpeechToTextProvider,
    StreamingTextProvider,
    StructuredOutputProvider,
    TextGenerationProvider,
    TextToSpeechProvider,
)
from app.ai.types import AudioChunk, ChatMessage, TextGenerationResult, TranscriptResult

T = TypeVar("T", bound=BaseModel)


def _mock_payload(response_model: type[BaseModel]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name, field in response_model.model_fields.items():
        if not field.is_required():
            continue
        if name.endswith("_text") or name == "question_text":
            payload[name] = "Mock generated text for automated tests."
        elif name.endswith("_tag") or name == "topic_tag":
            payload[name] = "mock_topic"
        elif field.annotation is bool:
            payload[name] = False
        elif field.annotation is int:
            payload[name] = 1
        else:
            payload[name] = f"mock-{name}"
    return payload


class MockTextGenerationProvider:
    async def generate_text(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> TextGenerationResult:
        _ = temperature
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return TextGenerationResult(
            text=f"Mock response to: {last_user[:120]}",
            model=model or "mock-llm",
        )


class MockStructuredOutputProvider:
    async def generate_structured(
        self,
        messages: list[ChatMessage] | list[dict[str, str]],
        response_model: type[T],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> T:
        _ = messages, model, temperature
        if not issubclass(response_model, BaseModel):
            raise TypeError("response_model must be a Pydantic BaseModel subclass")
        return response_model.model_validate(_mock_payload(response_model))


class MockStreamingTextProvider:
    async def stream_text(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        _ = model, temperature
        result = await MockTextGenerationProvider().generate_text(messages)
        for word in result.text.split():
            yield word + " "


class MockSpeechToTextProvider:
    async def transcribe(
        self,
        audio: bytes,
        *,
        mime_type: str = "audio/wav",
        language: str | None = None,
    ) -> TranscriptResult:
        _ = mime_type, language
        return TranscriptResult(text=f"mock transcript ({len(audio)} bytes)", confidence=0.99)


class MockTextToSpeechProvider:
    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        response_format: str = "pcm",
    ) -> AsyncIterator[AudioChunk]:
        _ = voice, response_format
        payload = f"mock-audio:{text}".encode("utf-8")
        yield AudioChunk(data=payload, seq=0, is_final=True)


class MockLLMProvider(MockStructuredOutputProvider):
    """Backward-compatible mock structured LLM provider."""
