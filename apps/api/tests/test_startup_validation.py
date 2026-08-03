import pytest

from app.config import Settings
from app.core.startup import validate_settings


def test_validate_settings_allows_development_defaults() -> None:
    settings = Settings(app_env="development")
    validate_settings(settings)


def test_validate_settings_rejects_production_with_default_db() -> None:
    settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://postgres:postgres@db:5432/voice_negotiator",
        cors_origins=["https://app.example.com"],
    )

    with pytest.raises(RuntimeError, match="default postgres credentials"):
        validate_settings(settings)


def test_validate_settings_requires_openai_key_in_production() -> None:
    settings = Settings(
        app_env="production",
        ai_provider="openai",
        openai_api_key=None,
        database_url="postgresql+psycopg://app:secret@db:5432/voice_negotiator",
        cors_origins=["https://app.example.com"],
    )

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        validate_settings(settings)
