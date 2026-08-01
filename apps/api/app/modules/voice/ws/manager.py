import logging
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class VoiceConnectionManager:
    """Tracks active voice WebSocket connections (one per session in MVP)."""

    def __init__(self) -> None:
        self._connections: dict[UUID, WebSocket] = {}

    async def register(self, session_id: UUID, websocket: WebSocket) -> None:
        existing = self._connections.get(session_id)
        if existing is not None:
            logger.warning(
                "Replacing existing voice connection for session",
                extra={"component": "voice_manager", "session_id": str(session_id)},
            )
        self._connections[session_id] = websocket

    def unregister(self, session_id: UUID) -> None:
        self._connections.pop(session_id, None)

    def is_connected(self, session_id: UUID) -> bool:
        return session_id in self._connections
