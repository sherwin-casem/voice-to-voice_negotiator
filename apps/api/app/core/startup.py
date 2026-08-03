import logging

from app.config import Settings

logger = logging.getLogger(__name__)

_DEFAULT_DB_MARKER = "postgres:postgres@"


def validate_settings(settings: Settings) -> None:
    """Fail fast when production configuration is incomplete or unsafe."""
    if not settings.is_production:
        return

    errors: list[str] = []

    if settings.debug:
        errors.append("DEBUG must be false in production")

    if settings.ai_provider == "openai" and not settings.openai_api_key:
        errors.append("OPENAI_API_KEY is required when AI_PROVIDER=openai")

    if _DEFAULT_DB_MARKER in settings.database_url:
        errors.append("DATABASE_URL must not use default postgres credentials in production")

    if not settings.cors_origins:
        errors.append("CORS_ORIGINS must include at least one allowed origin")

    localhost_only = all(
        origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")
        for origin in settings.cors_origins
    )
    if localhost_only:
        errors.append("CORS_ORIGINS must not be localhost-only in production")

    if errors:
        message = "Production configuration invalid:\n" + "\n".join(f"  - {item}" for item in errors)
        raise RuntimeError(message)

    logger.info("Production configuration validated", extra={"component": "startup"})
