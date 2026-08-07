"""Per-task channel for propagating token usage from providers to callers.

Structured-output providers return only the parsed model, so usage metadata
travels out-of-band via a contextvar. Each asyncio task gets its own copy of
the context, so concurrent evaluator agents never see each other's usage.
"""

from contextvars import ContextVar

from app.ai.types import TokenUsage

_last_token_usage: ContextVar[TokenUsage | None] = ContextVar("last_token_usage", default=None)


def record_token_usage(usage: TokenUsage | None) -> None:
    """Called by providers after each LLM call."""
    _last_token_usage.set(usage)


def consume_token_usage() -> TokenUsage | None:
    """Return the usage recorded by the most recent LLM call in this task, and clear it."""
    usage = _last_token_usage.get()
    _last_token_usage.set(None)
    return usage
