"""WebSocket event type constants."""

# Client → server
SESSION_START = "session.start"
AUDIO_INPUT = "audio.input"
SPEECH_END = "speech.end"
SESSION_END = "session.end"

# Server → client
SESSION_READY = "session.ready"
TRANSCRIPT_PARTIAL = "transcript.partial"
TRANSCRIPT_FINAL = "transcript.final"
INTERVIEWER_THINKING = "interviewer.thinking"
INTERVIEWER_RESPONSE = "interviewer.response"
AUDIO_OUTPUT = "audio.output"
SESSION_ERROR = "session.error"
# Server confirmation uses the same event name as the client-initiated end event.
SESSION_ENDED = "session.end"

CLIENT_EVENT_TYPES = frozenset({SESSION_START, AUDIO_INPUT, SPEECH_END, SESSION_END})
SERVER_EVENT_TYPES = frozenset({
    SESSION_READY,
    TRANSCRIPT_PARTIAL,
    TRANSCRIPT_FINAL,
    INTERVIEWER_THINKING,
    INTERVIEWER_RESPONSE,
    AUDIO_OUTPUT,
    SESSION_ERROR,
    SESSION_ENDED,
})
