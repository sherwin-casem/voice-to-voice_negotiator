from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.voice.protocol.types import (
    AUDIO_INPUT,
    AUDIO_OUTPUT,
    INTERVIEWER_RESPONSE,
    INTERVIEWER_THINKING,
    OUTPUT_CANCEL,
    SESSION_END,
    SESSION_ENDED,
    SESSION_ERROR,
    SESSION_READY,
    SESSION_START,
    SPEECH_END,
    TRANSCRIPT_FINAL,
    TRANSCRIPT_PARTIAL,
)


class WSEnvelope(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    timestamp_ms: int | None = None


class AudioFormat(BaseModel):
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    encoding: str = Field(default="pcm_s16le")
    channels: int = Field(default=1, ge=1, le=2)


class SessionStartPayload(BaseModel):
    session_id: UUID
    audio_format: AudioFormat = Field(default_factory=AudioFormat)


class AudioInputPayload(BaseModel):
    seq: int = Field(ge=0)
    data: str = Field(min_length=1, description="Base64-encoded audio chunk")
    timestamp_ms: int = Field(ge=0)

    @field_validator("data")
    @classmethod
    def validate_base64(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("data must not be empty")
        return value


class SpeechEndPayload(BaseModel):
    timestamp_ms: int = Field(ge=0)


class SessionEndPayload(BaseModel):
    reason: str = Field(default="user_ended", max_length=100)


class OutputCancelPayload(BaseModel):
    """Barge-in request; no fields required."""


class SessionReadyPayload(BaseModel):
    session_id: UUID
    status: str
    question_count: int = Field(ge=0)


class TranscriptPartialPayload(BaseModel):
    text: str
    seq: int = Field(default=0, ge=0)


class TranscriptFinalPayload(BaseModel):
    text: str
    question_id: UUID
    turn_id: UUID | None = None


class InterviewerThinkingPayload(BaseModel):
    question_id: UUID | None = None


class InterviewerResponsePayload(BaseModel):
    question_id: UUID
    text: str
    topic_tag: str | None = None
    should_end_session: bool = False


class AudioOutputPayload(BaseModel):
    seq: int = Field(ge=0)
    data: str = Field(description="Base64-encoded audio chunk; may be empty on a final marker")
    encoding: str = "pcm_s16le"
    sample_rate: int = 16000
    is_final: bool = False

    @model_validator(mode="after")
    def validate_data_presence(self) -> "AudioOutputPayload":
        if not self.data and not self.is_final:
            raise ValueError("data must not be empty on non-final audio chunks")
        return self


class SessionErrorPayload(BaseModel):
    code: str
    message: str
    recoverable: bool = True


class SessionEndedPayload(BaseModel):
    reason: str
    status: str


CLIENT_PAYLOAD_MODELS: dict[str, type[BaseModel]] = {
    SESSION_START: SessionStartPayload,
    AUDIO_INPUT: AudioInputPayload,
    SPEECH_END: SpeechEndPayload,
    SESSION_END: SessionEndPayload,
    OUTPUT_CANCEL: OutputCancelPayload,
}

SERVER_PAYLOAD_MODELS: dict[str, type[BaseModel]] = {
    SESSION_READY: SessionReadyPayload,
    TRANSCRIPT_PARTIAL: TranscriptPartialPayload,
    TRANSCRIPT_FINAL: TranscriptFinalPayload,
    INTERVIEWER_THINKING: InterviewerThinkingPayload,
    INTERVIEWER_RESPONSE: InterviewerResponsePayload,
    AUDIO_OUTPUT: AudioOutputPayload,
    SESSION_ERROR: SessionErrorPayload,
    SESSION_ENDED: SessionEndedPayload,
}
