import pytest

from app.ai.errors import AIConfigurationError
from app.ai.providers.factory import build_ai_providers
from app.config import Settings


def test_build_mock_providers_by_default() -> None:
    providers = build_ai_providers(Settings(ai_provider="mock"))
    assert providers.text is not None
    assert providers.structured is not None
    assert providers.streaming is not None
    assert providers.stt is not None
    assert providers.tts is not None


def test_build_openai_providers_requires_api_key() -> None:
    with pytest.raises(AIConfigurationError):
        build_ai_providers(Settings(ai_provider="openai", openai_api_key=None))
