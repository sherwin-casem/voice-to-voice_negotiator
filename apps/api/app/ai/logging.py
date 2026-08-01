import logging
from typing import Any

logger = logging.getLogger(__name__)


def log_ai_event(level: int, message: str, *, operation: str, provider: str, **fields: Any) -> None:
    extra = {
        "component": "ai",
        "operation": operation,
        "provider": provider,
        **fields,
    }
    logger.log(level, message, extra=extra)
