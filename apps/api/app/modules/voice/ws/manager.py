import logging
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

# Close code for a connection superseded by a newer one for the same session.
SUPERSEDED_CLOSE_CODE = 4000


class VoiceConnectionManager:
    """Tracks active voice WebSocket connections (one per session in MVP)."""

    def __init__(self) -> None:
        self._connections: dict[UUID, WebSocket] = {}
        self._sessions_by_user: dict[UUID, set[UUID]] = {}
        self._user_by_session: dict[UUID, UUID] = {}

    def user_connection_count(self, user_id: UUID) -> int:
        return len(self._sessions_by_user.get(user_id, ()))

    async def register(
        self, session_id: UUID, websocket: WebSocket, user_id: UUID | None = None
    ) -> None:
        existing = self._connections.get(session_id)
        if existing is not None and existing is not websocket:
            logger.warning(
                "Closing superseded voice connection for session",
                extra={"component": "voice_manager", "session_id": str(session_id)},
            )
            try:
                if existing.client_state == WebSocketState.CONNECTED:
                    await existing.close(code=SUPERSEDED_CLOSE_CODE)
            except Exception:  # noqa: BLE001 - old socket may already be dead
                logger.debug(
                    "Superseded connection was already closed",
                    extra={"component": "voice_manager", "session_id": str(session_id)},
                )
        self._connections[session_id] = websocket
        if user_id is not None:
            self._user_by_session[session_id] = user_id
            self._sessions_by_user.setdefault(user_id, set()).add(session_id)

    def unregister(self, session_id: UUID, websocket: WebSocket | None = None) -> None:
        # Never drop a newer connection that replaced this one.
        if websocket is not None and self._connections.get(session_id) is not websocket:
            return
        self._connections.pop(session_id, None)
        user_id = self._user_by_session.pop(session_id, None)
        if user_id is not None:
            sessions = self._sessions_by_user.get(user_id)
            if sessions is not None:
                sessions.discard(session_id)
                if not sessions:
                    del self._sessions_by_user[user_id]

    def is_connected(self, session_id: UUID) -> bool:
        return session_id in self._connections
