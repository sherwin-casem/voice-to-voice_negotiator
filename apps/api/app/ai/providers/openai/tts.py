from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from app.ai.logging import log_ai_event
from app.ai.providers.openai._client import OpenAIClientFactory, OpenAISettings, map_openai_exception
from app.ai.types import AudioChunk

PROVIDER = "openai"
logger = logging.getLogger(__name__)


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
                seq = 0
                async for chunk in response.iter_bytes():
                    if not chunk:
                        continue
                    yield AudioChunk(data=chunk, seq=seq, is_final=False)
                    seq += 1
                if seq > 0:
                    yield AudioChunk(data=b"", seq=seq, is_final=True)
                else:
                    yield AudioChunk(data=b"", seq=0, is_final=True)
        except Exception as exc:  # noqa: BLE001
            raise map_openai_exception(exc) from exc
