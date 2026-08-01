import json
import uuid

import pytest

from app.modules.voice.protocol.parser import ProtocolValidationError, parse_client_envelope
from app.modules.voice.protocol.types import AUDIO_INPUT, SESSION_START, SPEECH_END


def test_parse_session_start_event() -> None:
    session_id = uuid.uuid4()
    envelope, payload = parse_client_envelope(
        {
            "type": SESSION_START,
            "payload": {
                "session_id": str(session_id),
                "audio_format": {"sample_rate": 16000, "encoding": "pcm_s16le", "channels": 1},
            },
            "request_id": "req-1",
        }
    )

    assert envelope.type == SESSION_START
    assert payload.session_id == session_id
    assert payload.audio_format.sample_rate == 16000


def test_parse_audio_input_requires_base64_data() -> None:
    with pytest.raises(ProtocolValidationError, match="Invalid payload"):
        parse_client_envelope(
            {
                "type": AUDIO_INPUT,
                "payload": {"seq": 0, "data": "", "timestamp_ms": 1},
            }
        )


def test_parse_unknown_event_type_rejected() -> None:
    with pytest.raises(ProtocolValidationError, match="Unsupported client event"):
        parse_client_envelope({"type": "unknown.event", "payload": {}})


def test_parse_invalid_json_rejected() -> None:
    with pytest.raises(ProtocolValidationError, match="Malformed"):
        parse_client_envelope("{not-json")


def test_parse_speech_end_event() -> None:
    envelope, payload = parse_client_envelope(
        json.dumps({"type": SPEECH_END, "payload": {"timestamp_ms": 1234}})
    )
    assert envelope.type == SPEECH_END
    assert payload.timestamp_ms == 1234
