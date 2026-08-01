import pytest
from pydantic import BaseModel, Field

from app.ai.providers.factory import build_ai_providers
from app.ai.types import ChatMessage
from app.config import Settings


@pytest.mark.asyncio
async def test_mock_text_generation_provider() -> None:
    providers = build_ai_providers(Settings(ai_provider="mock"))
    result = await providers.text.generate_text(
        [ChatMessage(role="user", content="Hello there")],
    )
    assert "Hello there" in result.text
    assert result.model == "mock-llm"


@pytest.mark.asyncio
async def test_mock_streaming_text_provider() -> None:
    providers = build_ai_providers(Settings(ai_provider="mock"))
    chunks: list[str] = []
    async for piece in providers.streaming.stream_text([ChatMessage(role="user", content="Hi")]):
        chunks.append(piece)
    assert "".join(chunks).startswith("Mock response")


@pytest.mark.asyncio
async def test_mock_structured_output_provider() -> None:
    class SampleOutput(BaseModel):
        summary: str = Field(min_length=3)
        score: int

    providers = build_ai_providers(Settings(ai_provider="mock"))
    result = await providers.structured.generate_structured(
        [ChatMessage(role="user", content="Evaluate this")],
        SampleOutput,
    )
    assert isinstance(result, SampleOutput)
    assert result.score == 1


@pytest.mark.asyncio
async def test_mock_stt_and_tts_providers() -> None:
    providers = build_ai_providers(Settings(ai_provider="mock"))
    transcript = await providers.stt.transcribe(b"abc")
    assert "mock transcript" in transcript.text

    chunks = []
    async for chunk in providers.tts.synthesize("Hello"):
        chunks.append(chunk)
    assert chunks[-1].is_final is True
    assert b"mock-audio:Hello" in chunks[0].data
