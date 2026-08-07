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
        usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7, total_tokens=18),
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

    from app.ai.usage import consume_token_usage

    usage = consume_token_usage()
    assert usage is not None
    assert usage.total_tokens == 18


@pytest.mark.asyncio
async def test_openai_structured_output_repair_retry() -> None:
    """A parse failure triggers exactly one repair attempt with a corrective message."""
    providers = build_ai_providers(
        Settings(ai_provider="openai", openai_api_key="test-key", ai_max_retries=0),
    )
    parsed = SampleOutput(summary="Recovered summary")
    failed_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=None))],
        usage=None,
    )
    repaired_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))],
        usage=None,
    )

    with patch("app.ai.providers.openai.llm.OpenAIClientFactory.create") as create:
        client = MagicMock()
        client.beta.chat.completions.parse = AsyncMock(
            side_effect=[failed_response, repaired_response]
        )
        create.return_value = client

        result = await providers.structured.generate_structured(
            [ChatMessage(role="user", content="Summarize")],
            SampleOutput,
        )

    assert result.summary == "Recovered summary"
    assert client.beta.chat.completions.parse.await_count == 2
    repair_messages = client.beta.chat.completions.parse.await_args.kwargs["messages"]
    assert "could not be parsed" in repair_messages[-1]["content"]


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
            chunks.append(chunk)

    assert [chunk.data for chunk in chunks] == [b"chunk-1", b"chunk-2"]
    # The final marker must ride on the last data-carrying chunk, and the
    # provider must advertise its true output rate (OpenAI PCM is 24 kHz).
    assert [chunk.is_final for chunk in chunks] == [False, True]
    assert all(chunk.sample_rate == 24_000 for chunk in chunks)
