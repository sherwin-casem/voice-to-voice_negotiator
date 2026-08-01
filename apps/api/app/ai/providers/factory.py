from dataclasses import dataclass

from app.ai.providers.base import (
    SpeechToTextProvider,
    StreamingTextProvider,
    StructuredOutputProvider,
    TextGenerationProvider,
    TextToSpeechProvider,
)
from app.ai.providers.mock import (
    MockSpeechToTextProvider,
    MockStreamingTextProvider,
    MockStructuredOutputProvider,
    MockTextGenerationProvider,
    MockTextToSpeechProvider,
)
from app.ai.providers.openai._client import (
    OpenAIClientFactory,
    OpenAISettings,
    get_openai_client_factory,
    get_openai_settings,
)
from app.ai.providers.openai import (
    OpenAISpeechToTextProvider,
    OpenAIStructuredOutputProvider,
    OpenAIStreamingTextProvider,
    OpenAITextGenerationProvider,
    OpenAITextToSpeechProvider,
)
from app.config import Settings, settings


@dataclass(frozen=True)
class AIProviders:
    text: TextGenerationProvider
    structured: StructuredOutputProvider
    streaming: StreamingTextProvider
    stt: SpeechToTextProvider
    tts: TextToSpeechProvider


def build_ai_providers(app_settings: Settings | None = None) -> AIProviders:
    resolved = app_settings or settings

    if resolved.ai_provider == "mock":
        return AIProviders(
            text=MockTextGenerationProvider(),
            structured=MockStructuredOutputProvider(),
            streaming=MockStreamingTextProvider(),
            stt=MockSpeechToTextProvider(),
            tts=MockTextToSpeechProvider(),
        )

    openai_settings = OpenAISettings.from_app_settings(resolved)
    client_factory = OpenAIClientFactory(openai_settings)
    return AIProviders(
        text=OpenAITextGenerationProvider(client_factory, openai_settings),
        structured=OpenAIStructuredOutputProvider(client_factory, openai_settings),
        streaming=OpenAIStreamingTextProvider(client_factory, openai_settings),
        stt=OpenAISpeechToTextProvider(client_factory, openai_settings),
        tts=OpenAITextToSpeechProvider(client_factory, openai_settings),
    )


def get_ai_providers() -> AIProviders:
    return build_ai_providers(settings)
