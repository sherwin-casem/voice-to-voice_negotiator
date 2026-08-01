from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

ChatRole = Literal["system", "user", "assistant", "developer"]


@dataclass(frozen=True)
class ChatMessage:
    role: ChatRole
    content: str

    def to_openai(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class TextGenerationResult:
    text: str
    model: str
    usage: TokenUsage | None = None


@dataclass(frozen=True)
class TranscriptResult:
    text: str
    confidence: float | None = None
    language: str | None = None
    is_final: bool = True


@dataclass(frozen=True)
class AudioChunk:
    data: bytes
    seq: int = 0
    is_final: bool = False


TextStream = AsyncIterator[str]
