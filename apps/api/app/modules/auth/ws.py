from uuid import UUID

from fastapi import Query, WebSocketException, status

from app.config import settings
from app.core.exceptions import UnauthorizedError
from app.modules.auth.service import decode_ws_ticket


def parse_ws_user_id(
    session_id: UUID,
    ticket: str | None = Query(default=None, alias="ticket"),
    user_id: str | None = Query(default=None, alias="user_id"),
) -> UUID:
    """Authenticate a voice WebSocket connection.

    Production path: a short-lived, session-bound ticket issued by
    POST /auth/ws-ticket. The bare ``user_id`` query parameter is a
    development-only convenience, gated the same way as the REST
    ``X-User-Id`` header.
    """
    if ticket:
        try:
            payload = decode_ws_ticket(ticket)
        except UnauthorizedError as exc:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=exc.message,
            ) from exc
        if payload.get("sid") != str(session_id):
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Ticket does not match this session",
            )
        return UUID(payload["sub"])

    if settings.allow_dev_user_header and settings.is_development and user_id:
        try:
            return UUID(user_id)
        except ValueError as exc:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid user_id",
            ) from exc

    raise WebSocketException(
        code=status.WS_1008_POLICY_VIOLATION,
        reason="Authentication required",
    )
