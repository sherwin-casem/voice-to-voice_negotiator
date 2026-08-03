import pytest

from app.ai.providers.mock import MockSpeechToTextProvider, MockTextToSpeechProvider
from app.modules.voice.providers.adapter import SpeechToTextAdapter, TextToSpeechAdapter


@pytest.mark.asyncio
async def test_stt_adapter_yields_final_transcript_for_batch_provider() -> None:
    adapter = SpeechToTextAdapter(MockSpeechToTextProvider(), simulate_partial=False)
    results = [item async for item in adapter.stream_transcribe(b"raw pcm bytes", sample_rate=16000)]

    assert len(results) == 1
    assert results[0].is_final is True
    assert "mock transcript" in results[0].text


@pytest.mark.asyncio
async def test_stt_adapter_can_simulate_partial_transcripts() -> None:
    adapter = SpeechToTextAdapter(MockSpeechToTextProvider(), simulate_partial=True)
    results = [item async for item in adapter.stream_transcribe(b"0123456789", sample_rate=16000)]

    assert len(results) == 2
    assert results[0].is_final is False
    assert results[1].is_final is True
    assert results[1].text.startswith(results[0].text)


@pytest.mark.asyncio
async def test_tts_adapter_streams_audio_chunks() -> None:
    adapter = TextToSpeechAdapter(MockTextToSpeechProvider())
    chunks = [chunk async for chunk in adapter.synthesize("Hello interviewer", sample_rate=16000)]

    assert len(chunks) >= 1
    assert chunks[-1].is_final is True
    assert chunks[0].data
