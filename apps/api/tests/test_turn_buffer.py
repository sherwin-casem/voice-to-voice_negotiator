import pytest

pytestmark = pytest.mark.feature

import base64

from app.modules.voice.pipeline.turn_buffer import TurnAudioBuffer


def test_turn_buffer_concatenates_chunks_in_sequence() -> None:
    buffer = TurnAudioBuffer()
    audio = b"hello-world"
    encoded = base64.b64encode(audio).decode("ascii")

    buffer.append(0, encoded)

    assert buffer.consume() == audio
    assert buffer.byte_count == 0


def test_turn_buffer_rejects_non_monotonic_sequence() -> None:
    buffer = TurnAudioBuffer()
    encoded = base64.b64encode(b"abc").decode("ascii")

    buffer.append(1, encoded)

    with pytest.raises(ValueError, match="sequence must increase"):
        buffer.append(1, encoded)
