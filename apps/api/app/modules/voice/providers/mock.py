import asyncio
import base64
import hashlib
from collections.abc import AsyncIterator

from app.modules.voice.providers.base import AudioChunk, TranscriptResult


class MockSpeechToTextProvider:
    """Deterministic STT for tests and local development."""

    async def transcribe(self, audio: bytes, *, sample_rate: int = 16000) -> TranscriptResult:
        await asyncio.sleep(0)
        text = _mock_transcript(audio)
        return TranscriptResult(text=text, confidence=0.95, is_final=True)

    async def stream_transcribe(
        self,
        audio: bytes,
        *,
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptResult]:
        full_text = _mock_transcript(audio)
        partial = full_text[: max(len(full_text) // 2, 1)]
        yield TranscriptResult(text=partial, confidence=0.7, is_final=False)
        await asyncio.sleep(0)
        yield TranscriptResult(text=full_text, confidence=0.95, is_final=True)


class MockTextToSpeechProvider:
    """Deterministic TTS that emits synthetic PCM chunks."""

    chunk_samples = 1600  # 100ms at 16kHz

    async def synthesize(
        self,
        text: str,
        *,
        sample_rate: int = 16000,
    ) -> AsyncIterator[AudioChunk]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        total_chunks = max(1, min(8, len(text) // 20 + 1))

        for seq in range(total_chunks):
            await asyncio.sleep(0)
            chunk = bytes([digest[seq % len(digest)]] * self.chunk_samples * 2)
            is_final = seq == total_chunks - 1
            yield AudioChunk(data=chunk, seq=seq, is_final=is_final, sample_rate=sample_rate)


def _mock_transcript(audio: bytes) -> str:
    if not audio:
        return "I don't have a detailed answer yet."
    digest = hashlib.sha256(audio).hexdigest()[:8]
    return f"Candidate answer transcript {digest}."
