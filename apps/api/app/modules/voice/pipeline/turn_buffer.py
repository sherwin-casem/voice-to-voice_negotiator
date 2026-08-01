import base64
from dataclasses import dataclass, field


@dataclass
class TurnAudioBuffer:
    sample_rate: int = 16000
    encoding: str = "pcm_s16le"
    channels: int = 1
    _chunks: list[bytes] = field(default_factory=list)
    _last_seq: int | None = None

    def append(self, seq: int, data_b64: str) -> None:
        if self._last_seq is not None and seq <= self._last_seq:
            raise ValueError(f"Audio sequence must increase (got {seq}, last {self._last_seq})")
        self._last_seq = seq
        self._chunks.append(base64.b64decode(data_b64))

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
