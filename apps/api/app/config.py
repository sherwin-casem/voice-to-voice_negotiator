from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ENV_FILE), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_json: bool = False

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/voice_negotiator"
    database_echo: bool = False

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    voice_provider: Literal["mock"] = "mock"
    ws_max_audio_chunk_bytes: int = 256_000

    ai_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: str | None = None
    openai_organization: str | None = None
    openai_base_url: str | None = None
    openai_llm_model: str = "gpt-4o-mini"
    openai_structured_model: str = "gpt-4o-mini"
    openai_streaming_model: str = "gpt-4o-mini"
    openai_stt_model: str = "gpt-4o-transcribe"
    openai_tts_model: str = "tts-1"
    openai_tts_voice: str = "alloy"
    ai_request_timeout_seconds: float = 60.0
    ai_max_retries: int = 2
    ai_retry_backoff_seconds: float = 0.5

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value  # type: ignore[return-value]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"


settings = Settings()
