import base64
from dataclasses import dataclass, field


@dataclass
class TurnAudioBuffer:
    sample_rate: int = 16000
    encoding: str = "pcm_s16le"
    channels: int = 1
    max_chunk_bytes: int = 256_000
    max_turn_bytes: int = 5_242_880
    _chunks: list[bytes] = field(default_factory=list)
    _last_seq: int | None = None

    def append(self, seq: int, data_b64: str) -> None:
        if self._last_seq is not None and seq <= self._last_seq:
            raise ValueError(f"Audio sequence must increase (got {seq}, last {self._last_seq})")
        chunk = base64.b64decode(data_b64)
        if len(chunk) > self.max_chunk_bytes:
            raise ValueError(
                f"Audio chunk exceeds maximum size of {self.max_chunk_bytes} bytes "
                f"(got {len(chunk)})"
            )
        if self.byte_count + len(chunk) > self.max_turn_bytes:
            raise ValueError(
                f"Turn audio exceeds maximum size of {self.max_turn_bytes} bytes"
            )
        self._last_seq = seq
        self._chunks.append(chunk)

    def reset(self) -> None:
        self._chunks.clear()
        self._last_seq = None

    @property
    def byte_count(self) -> int:
        return sum(len(chunk) for chunk in self._chunks)

    def consume(self) -> bytes:
        audio = b"".join(self._chunks)
        self.reset()
        return audio
