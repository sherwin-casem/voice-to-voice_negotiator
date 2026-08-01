from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TranscriptResult:
    text: str
    confidence: float | None = None
    is_final: bool = True


@dataclass(frozen=True)
class AudioChunk:
    data: bytes
    seq: int
    is_final: bool = False


class SpeechToTextProvider(Protocol):
    async def transcribe(self, audio: bytes, *, sample_rate: int = 16000) -> TranscriptResult: ...

    async def stream_transcribe(
        self,
        audio: bytes,
        *,
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptResult]: ...


class TextToSpeechProvider(Protocol):
    async def synthesize(
        self,
        text: str,
        *,
        sample_rate: int = 16000,
    ) -> AsyncIterator[AudioChunk]: ...
