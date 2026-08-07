from collections.abc import AsyncIterator

from app.ai.providers.base import SpeechToTextProvider as AISpeechToTextProvider
from app.ai.providers.base import TextToSpeechProvider as AITextToSpeechProvider
from app.modules.voice.audio import pcm_to_wav
from app.modules.voice.providers.base import AudioChunk, TranscriptResult


class SpeechToTextAdapter:
    """Adapts the shared AI STT provider to the voice pipeline streaming interface."""

    def __init__(
        self,
        provider: AISpeechToTextProvider,
        *,
        simulate_partial: bool = False,
    ) -> None:
        self._provider = provider
        self._simulate_partial = simulate_partial

    async def transcribe(self, audio: bytes, *, sample_rate: int = 16000) -> TranscriptResult:
        wav = pcm_to_wav(audio, sample_rate=sample_rate)
        result = await self._provider.transcribe(wav, mime_type="audio/wav")
        return TranscriptResult(
            text=result.text,
            confidence=result.confidence,
            is_final=True,
        )

    async def stream_transcribe(
        self,
        audio: bytes,
        *,
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptResult]:
        if self._simulate_partial:
            wav = pcm_to_wav(audio, sample_rate=sample_rate)
            result = await self._provider.transcribe(wav, mime_type="audio/wav")
            if len(result.text) > 1:
                partial_len = max(1, len(result.text) // 2)
                yield TranscriptResult(
                    text=result.text[:partial_len],
                    confidence=result.confidence,
                    is_final=False,
                )
            yield TranscriptResult(
                text=result.text,
                confidence=result.confidence,
                is_final=True,
            )
            return

        result = await self.transcribe(audio, sample_rate=sample_rate)
        yield result


class TextToSpeechAdapter:
    """Adapts the shared AI TTS provider to the voice pipeline streaming interface."""

    def __init__(self, provider: AITextToSpeechProvider) -> None:
        self._provider = provider

    async def synthesize(
        self,
        text: str,
        *,
        sample_rate: int = 16000,
    ) -> AsyncIterator[AudioChunk]:
        # The provider dictates the actual output rate (e.g. OpenAI PCM is
        # 24 kHz); propagate it so clients play audio at the correct speed.
        _ = sample_rate
        async for chunk in self._provider.synthesize(text, response_format="pcm"):
            yield AudioChunk(
                data=chunk.data,
                seq=chunk.seq,
                is_final=chunk.is_final,
                sample_rate=chunk.sample_rate,
            )
