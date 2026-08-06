from uuid import UUID

from fastapi import Query, WebSocket, WebSocketException, status

from app.modules.auth.service import decode_access_token


def parse_ws_user_id(
    access_token: str | None = Query(default=None, alias="access_token"),
    user_id: str | None = Query(default=None, alias="user_id"),
) -> UUID:
    if access_token:
        payload = decode_access_token(access_token)
        return UUID(payload["sub"])

    if user_id:
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
