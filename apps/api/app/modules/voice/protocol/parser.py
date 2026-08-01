import json
from typing import Any

from pydantic import BaseModel, ValidationError

from app.modules.voice.protocol.events import CLIENT_PAYLOAD_MODELS, WSEnvelope
from app.modules.voice.protocol.types import CLIENT_EVENT_TYPES


class ProtocolValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def parse_client_envelope(raw: str | bytes | dict[str, Any]) -> tuple[WSEnvelope, BaseModel]:
    try:
        if isinstance(raw, (str, bytes)):
            data = json.loads(raw)
        else:
            data = raw
        envelope = WSEnvelope.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ProtocolValidationError("INVALID_ENVELOPE", "Malformed WebSocket message envelope") from exc

    if envelope.type not in CLIENT_EVENT_TYPES:
        raise ProtocolValidationError("UNKNOWN_EVENT", f"Unsupported client event type: {envelope.type}")

    payload_model = CLIENT_PAYLOAD_MODELS[envelope.type]
    try:
        payload = payload_model.model_validate(envelope.payload)
    except ValidationError as exc:
        raise ProtocolValidationError("INVALID_PAYLOAD", f"Invalid payload for {envelope.type}") from exc

    return envelope, payload


def build_server_envelope(
    event_type: str,
    payload: BaseModel,
    *,
    request_id: str | None = None,
    timestamp_ms: int | None = None,
) -> dict[str, Any]:
    return WSEnvelope(
        type=event_type,
        payload=payload.model_dump(mode="json"),
        request_id=request_id,
        timestamp_ms=timestamp_ms,
    ).model_dump(mode="json", exclude_none=True)
