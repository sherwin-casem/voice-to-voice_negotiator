from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from app.ai.providers.factory import build_ai_providers
from app.ai.types import ChatMessage
from app.config import Settings


class SampleOutput(BaseModel):
    summary: str = Field(min_length=3)


@pytest.mark.asyncio
async def test_openai_text_generation_provider() -> None:
    providers = build_ai_providers(
        Settings(ai_provider="openai", openai_api_key="test-key", ai_max_retries=0),
    )
    mock_response = SimpleNamespace(
        model="gpt-4o-mini",
        choices=[SimpleNamespace(message=SimpleNamespace(content="Hello from OpenAI"))],
        usage=SimpleNamespace(prompt_tokens=3, completion_tokens=5, total_tokens=8),
    )

    with patch("app.ai.providers.openai.llm.OpenAIClientFactory.create") as create:
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        create.return_value = client

        result = await providers.text.generate_text([ChatMessage(role="user", content="Hi")])

    assert result.text == "Hello from OpenAI"
    assert result.usage is not None
    assert result.usage.total_tokens == 8


@pytest.mark.asyncio
async def test_openai_structured_output_provider() -> None:
    providers = build_ai_providers(
        Settings(ai_provider="openai", openai_api_key="test-key", ai_max_retries=0),
    )
    parsed = SampleOutput(summary="Structured summary")
    mock_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))],
    )

    with patch("app.ai.providers.openai.llm.OpenAIClientFactory.create") as create:
        client = MagicMock()
        client.beta.chat.completions.parse = AsyncMock(return_value=mock_response)
        create.return_value = client

        result = await providers.structured.generate_structured(
            [ChatMessage(role="user", content="Summarize")],
            SampleOutput,
        )

    assert result.summary == "Structured summary"


@pytest.mark.asyncio
async def test_openai_stt_provider() -> None:
    providers = build_ai_providers(
        Settings(ai_provider="openai", openai_api_key="test-key", ai_max_retries=0),
    )
    mock_response = SimpleNamespace(text="transcribed text")

    with patch("app.ai.providers.openai.stt.OpenAIClientFactory.create") as create:
        client = MagicMock()
        client.audio.transcriptions.create = AsyncMock(return_value=mock_response)
        create.return_value = client

        result = await providers.stt.transcribe(b"audio-bytes")

    assert result.text == "transcribed text"


@pytest.mark.asyncio
async def test_openai_tts_provider_streams_chunks() -> None:
    providers = build_ai_providers(
        Settings(ai_provider="openai", openai_api_key="test-key", ai_max_retries=0),
    )

    class FakeStream:
        async def iter_bytes(self):
            yield b"chunk-1"
            yield b"chunk-2"

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    with patch("app.ai.providers.openai.tts.OpenAIClientFactory.create") as create:
        client = MagicMock()
        client.audio.speech.with_streaming_response.create.return_value = FakeStream()
        create.return_value = client

        chunks = []
        async for chunk in providers.tts.synthesize("Hello"):
            if chunk.data:
                chunks.append(chunk.data)

    assert chunks == [b"chunk-1", b"chunk-2"]
