from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from app.ai.logging import log_ai_event
from app.ai.providers.openai._client import OpenAIClientFactory, OpenAISettings, map_openai_exception
from app.ai.types import AudioChunk

PROVIDER = "openai"
logger = logging.getLogger(__name__)

# OpenAI TTS "pcm" responses are always 24 kHz, 16-bit signed little-endian, mono.
OPENAI_PCM_SAMPLE_RATE = 24_000


class OpenAITextToSpeechProvider:
    def __init__(self, client_factory: OpenAIClientFactory, openai_settings: OpenAISettings) -> None:
        self._client_factory = client_factory
        self._settings = openai_settings

    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        response_format: str = "pcm",
    ) -> AsyncIterator[AudioChunk]:
        selected_model = self._settings.tts_model
        selected_voice = voice or self._settings.tts_voice

        log_ai_event(
            logging.INFO,
            "Synthesizing speech",
            operation="synthesize",
            provider=PROVIDER,
            model=selected_model,
            voice=selected_voice,
            text_length=len(text),
        )

        client = self._client_factory.create()
        try:
            async with client.audio.speech.with_streaming_response.create(
                model=selected_model,
                voice=selected_voice,
                input=text,
                response_format=response_format,  # type: ignore[arg-type]
            ) as response:
                # One chunk of lookahead so the last non-empty chunk can be
                # flagged is_final (consumers require final chunks to carry data).
                seq = 0
                pending: bytes | None = None
                async for chunk in response.iter_bytes():
                    if not chunk:
                        continue
                    if pending is not None:
                        yield AudioChunk(
                            data=pending,
                            seq=seq,
                            is_final=False,
                            sample_rate=OPENAI_PCM_SAMPLE_RATE,
                        )
                        seq += 1
                    pending = chunk
                if pending is not None:
                    yield AudioChunk(
                        data=pending,
                        seq=seq,
                        is_final=True,
                        sample_rate=OPENAI_PCM_SAMPLE_RATE,
                    )
        except Exception as exc:  # noqa: BLE001
            raise map_openai_exception(exc) from exc
