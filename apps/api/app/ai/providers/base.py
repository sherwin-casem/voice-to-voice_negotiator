from collections.abc import AsyncIterator
from typing import Protocol, TypeVar

from pydantic import BaseModel

from app.ai.types import (
    AudioChunk,
    ChatMessage,
    TextGenerationResult,
    TranscriptResult,
)

T = TypeVar("T", bound=BaseModel)


class TextGenerationProvider(Protocol):
    async def generate_text(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> TextGenerationResult: ...


class StructuredOutputProvider(Protocol):
    async def generate_structured(
        self,
        messages: list[ChatMessage] | list[dict[str, str]],
        response_model: type[T],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> T: ...


class StreamingTextProvider(Protocol):
    async def stream_text(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[str]: ...


class SpeechToTextProvider(Protocol):
    async def transcribe(
        self,
        audio: bytes,
        *,
        mime_type: str = "audio/wav",
        language: str | None = None,
    ) -> TranscriptResult: ...


class TextToSpeechProvider(Protocol):
    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        response_format: str = "pcm",
    ) -> AsyncIterator[AudioChunk]: ...


# Backward-compatible alias used by interview scaffolding.
LLMProvider = StructuredOutputProvider
