import base64

import pytest

from app.modules.voice.pipeline.turn_buffer import TurnAudioBuffer


def test_turn_buffer_rejects_oversized_chunk() -> None:
    buffer = TurnAudioBuffer(max_chunk_bytes=4)
    oversized = base64.b64encode(b"hello").decode()

    with pytest.raises(ValueError, match="chunk exceeds maximum"):
        buffer.append(0, oversized)


def test_turn_buffer_rejects_oversized_turn() -> None:
    buffer = TurnAudioBuffer(max_chunk_bytes=10, max_turn_bytes=3)
    buffer.append(0, "YWFh")  # "aaa" = 3 bytes at limit

    with pytest.raises(ValueError, match="Turn audio exceeds"):
        buffer.append(1, "YQ==")


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
