from pathlib import Path
from typing import Literal
import json

from pydantic import Field
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
    cors_origins_raw: str = Field(
        default="http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )

    ws_max_audio_chunk_bytes: int = 256_000
    ws_max_turn_audio_bytes: int = 5_242_880
    max_upload_bytes: int = 512_000

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

    @property
    def cors_origins(self) -> list[str]:
        value = self.cors_origins_raw.strip()
        if not value:
            return []
        if value.startswith("["):
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
            return [str(parsed)]
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    jwt_secret: str = "change-me-in-production"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30
    ws_ticket_ttl_seconds: int = 60
    # How long an ACTIVE session survives a transient disconnect before being
    # marked abandoned.
    ws_reconnect_grace_seconds: float = 30.0

    evaluation_timeout_seconds: float = 240.0

    rate_limit_enabled: bool = True
    auth_rate_limit_per_minute: int = 10
    ws_connect_rate_limit_per_minute: int = 20
    ws_max_connections_per_user: int = 3
    auth_cookie_name: str = "vvn_refresh_token"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    allow_dev_user_header: bool = True


settings = Settings()
