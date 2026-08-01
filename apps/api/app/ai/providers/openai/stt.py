from __future__ import annotations

import io
import logging
from collections.abc import AsyncIterator

from app.ai.logging import log_ai_event
from app.ai.providers.openai._client import OpenAIClientFactory, OpenAISettings, map_openai_exception
from app.ai.retry import run_with_retry
from app.ai.types import TranscriptResult

PROVIDER = "openai"
logger = logging.getLogger(__name__)


class OpenAISpeechToTextProvider:
    def __init__(self, client_factory: OpenAIClientFactory, openai_settings: OpenAISettings) -> None:
        self._client_factory = client_factory
        self._settings = openai_settings

    async def transcribe(
        self,
        audio: bytes,
        *,
        mime_type: str = "audio/wav",
        language: str | None = None,
    ) -> TranscriptResult:
        selected_model = self._settings.stt_model
        filename = _filename_for_mime_type(mime_type)

        async def operation() -> TranscriptResult:
            client = self._client_factory.create()
            try:
                response = await client.audio.transcriptions.create(
                    model=selected_model,
                    file=(filename, io.BytesIO(audio)),
                    language=language,
                    response_format="json",
                )
            except Exception as exc:  # noqa: BLE001
                raise map_openai_exception(exc) from exc

            text = getattr(response, "text", str(response))
            return TranscriptResult(text=text, language=language)

        log_ai_event(
            logging.INFO,
            "Transcribing audio",
            operation="transcribe",
            provider=PROVIDER,
            model=selected_model,
            audio_bytes=len(audio),
        )
        return await run_with_retry(
            operation,
            max_retries=self._settings.max_retries,
            backoff_seconds=self._settings.retry_backoff_seconds,
        )


def _filename_for_mime_type(mime_type: str) -> str:
    if "mpeg" in mime_type or mime_type.endswith("/mp3"):
        return "audio.mp3"
    if "webm" in mime_type:
        return "audio.webm"
    return "audio.wav"
