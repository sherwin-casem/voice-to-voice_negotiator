import pytest

from app.modules.voice.pipeline.turn_buffer import TurnAudioBuffer


def test_turn_buffer_requires_monotonic_sequence() -> None:
    buffer = TurnAudioBuffer()
    buffer.append(0, "YQ==")  # "a"

    with pytest.raises(ValueError, match="sequence must increase"):
        buffer.append(0, "Yg==")

    buffer.append(1, "Yg==")
    assert buffer.byte_count > 0


def test_turn_buffer_consume_resets_state() -> None:
    buffer = TurnAudioBuffer()
    buffer.append(0, "YQ==")
    buffer.append(1, "Yg==")

    audio = buffer.consume()

    assert audio == b"ab"
    assert buffer.byte_count == 0

    buffer.append(0, "Yw==")
    assert buffer.consume() == b"c"
