from dataclasses import dataclass

from app.ai.providers.factory import build_ai_providers
from app.config import Settings, settings
from app.modules.voice.providers.adapter import SpeechToTextAdapter, TextToSpeechAdapter
from app.modules.voice.providers.base import SpeechToTextProvider, TextToSpeechProvider
from app.modules.voice.providers.mock import MockSpeechToTextProvider, MockTextToSpeechProvider


@dataclass(frozen=True)
class VoiceProviders:
    stt: SpeechToTextProvider
    tts: TextToSpeechProvider


def build_voice_providers(app_settings: Settings | None = None) -> VoiceProviders:
    """Build replaceable voice-layer STT/TTS providers.

    Mock mode uses deterministic voice mocks with streaming partial transcripts.
    OpenAI mode adapts the shared AI provider layer without changing WebSocket code.
    """
    resolved = app_settings or settings

    if resolved.ai_provider == "mock":
        return VoiceProviders(
            stt=MockSpeechToTextProvider(),
            tts=MockTextToSpeechProvider(),
        )

    ai = build_ai_providers(resolved)
    return VoiceProviders(
        stt=SpeechToTextAdapter(ai.stt, simulate_partial=False),
        tts=TextToSpeechAdapter(ai.tts),
    )


def get_voice_providers() -> VoiceProviders:
    return build_voice_providers(settings)
