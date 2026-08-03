# WebSocket Voice Protocol

**Status:** MVP  
**Endpoint:** `WS /api/v1/ws/interview/{session_id}?user_id={uuid}`  
**Transport:** JSON text frames with typed event envelopes

This document defines the real-time voice protocol for the Voice-to-Voice Interview Negotiator backend. It separates **audio transport** (capture, STT, TTS streaming) from **interview business logic** (session state, questions, answers), which is handled by the existing REST + orchestrator layer and invoked by the voice pipeline.

---

## Connection

### URL

```
ws://localhost:8000/api/v1/ws/interview/{session_id}?user_id={user_uuid}
```

| Parameter | Location | Description |
|-----------|----------|-------------|
| `session_id` | path | Interview session UUID (must exist and belong to the user) |
| `user_id` | query | User UUID (dev placeholder until JWT auth is implemented) |

### Lifecycle

1. Client opens WebSocket.
2. Server accepts and sends `session.ready` with current session status.
3. Client sends `session.start` to begin the voice interview.
4. Server sends the first interviewer question (`interviewer.response`) and TTS audio (`audio.output` chunks).
5. Client streams answer audio via `audio.input` and signals turn completion with `speech.end`.
6. Server emits STT events, updates interview state, generates the next question, and streams TTS back.
7. Client or server ends the session with `session.end`.

### Disconnect handling

- If the client disconnects while the session is **active**, the backend marks the session **abandoned** with reason `disconnect`.
- In-flight turn processing tasks are cancelled.
- Partial audio buffers are discarded.

---

## Envelope format

All messages use the same envelope:

```json
{
  "type": "event.name",
  "payload": {},
  "request_id": "optional-correlation-id",
  "timestamp_ms": 1710000000123
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `type` | yes | Event type string (see tables below) |
| `payload` | yes | Event-specific object (may be `{}`) |
| `request_id` | no | Client-supplied correlation ID echoed when provided |
| `timestamp_ms` | no | Unix epoch milliseconds (typically set by server) |

Invalid envelopes or payloads receive a `session.error` event with `recoverable: true`.

---

## Client → server events

### `session.start`

Begin the voice interview on this connection.

```json
{
  "type": "session.start",
  "payload": {
    "session_id": "uuid",
    "audio_format": {
      "sample_rate": 16000,
      "encoding": "pcm_s16le",
      "channels": 1
    }
  }
}
```

**Requirements:**
- Session must be `configured` (or `active` with no questions yet).
- `session_id` must match the WebSocket path.
- May only be sent once per connection.

**Server actions:**
- Activates the interview via the orchestrator.
- Emits the first `interviewer.response` and `audio.output` stream.

---

### `audio.input`

Stream a microphone audio chunk to the backend.

```json
{
  "type": "audio.input",
  "payload": {
    "seq": 0,
    "data": "<base64>",
    "timestamp_ms": 1710000000456,
    "is_final_chunk": false
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `seq` | int | Monotonically increasing sequence number per turn |
| `data` | string | Base64-encoded audio bytes |
| `timestamp_ms` | int | Client capture timestamp |
| `is_final_chunk` | bool | Optional hint that this is the last chunk of a turn |

**Audio format (MVP):** PCM 16-bit little-endian, 16 kHz, mono (`pcm_s16le`).

Chunks are buffered server-side until `speech.end`.

---

### `speech.end`

Signal that the candidate finished speaking for the current turn.

```json
{
  "type": "speech.end",
  "payload": {
    "timestamp_ms": 1710000001300
  }
}
```

**Server actions (async, non-blocking):**
1. Run STT on buffered audio (`transcript.partial` → `transcript.final`).
2. Persist answer via interview orchestrator.
3. Emit `interviewer.thinking`.
4. Generate next question and emit `interviewer.response` + `audio.output`.

---

### `session.end`

End the interview from the client.

```json
{
  "type": "session.end",
  "payload": {
    "reason": "user_ended"
  }
}
```

**Server actions:**
- Ends the interview session via orchestrator.
- Sends confirming `session.end` with final status.
- Closes the WebSocket.

---

## Server → client events

### `session.ready`

Sent immediately after the WebSocket is accepted.

```json
{
  "type": "session.ready",
  "payload": {
    "session_id": "uuid",
    "status": "configured",
    "question_count": 0
  }
}
```

---

### `transcript.partial`

Interim speech-to-text result while processing a turn.

```json
{
  "type": "transcript.partial",
  "payload": {
    "text": "I led a team of five engineers",
    "seq": 0
  }
}
```

---

### `transcript.final`

Final STT result for the completed candidate turn.

```json
{
  "type": "transcript.final",
  "payload": {
    "text": "I led a team of five engineers to deliver the platform migration.",
    "question_id": "uuid",
    "turn_id": "uuid"
  }
}
```

The answer is persisted against `question_id` before the next interviewer turn begins.

---

### `interviewer.thinking`

Indicates the backend is generating the next interviewer question.

```json
{
  "type": "interviewer.thinking",
  "payload": {
    "question_id": "uuid-of-answered-question"
  }
}
```

---

### `interviewer.response`

The interviewer's next question text.

```json
{
  "type": "interviewer.response",
  "payload": {
    "question_id": "uuid",
    "text": "What was the biggest technical challenge in that migration?",
    "topic_tag": "technical_depth",
    "should_end_session": false
  }
}
```

When `should_end_session` is `true`, the session will end after this turn's audio is delivered.

---

### `audio.output`

Streamed text-to-speech audio chunk for the current interviewer response.

```json
{
  "type": "audio.output",
  "payload": {
    "seq": 0,
    "data": "<base64>",
    "encoding": "pcm_s16le",
    "sample_rate": 16000,
    "is_final": false
  }
}
```

Play chunks in `seq` order. The last chunk has `is_final: true`.

---

### `session.error`

Structured error notification.

```json
{
  "type": "session.error",
  "payload": {
    "code": "NOT_STARTED",
    "message": "Send session.start before audio.input",
    "recoverable": true
  }
}
```

| Code | Typical cause |
|------|----------------|
| `INVALID_ENVELOPE` | Malformed JSON or envelope |
| `INVALID_PAYLOAD` | Payload failed schema validation |
| `UNKNOWN_EVENT` | Unsupported `type` |
| `NOT_STARTED` | Audio sent before `session.start` |
| `SESSION_MISMATCH` | Payload `session_id` ≠ path |
| `INVALID_AUDIO_SEQ` | Non-monotonic `audio.input` sequence |
| `EMPTY_AUDIO` | `speech.end` with no buffered audio |
| `PIPELINE_BUSY` | Previous turn still processing |
| `NO_ACTIVE_QUESTION` | No question to answer |
| `INVALID_STATE` | Interview session in wrong status |

---

### `session.end`

Server confirmation that the session has ended (also used as the client-initiated end event).

```json
{
  "type": "session.end",
  "payload": {
    "reason": "user_ended",
    "status": "completed"
  }
}
```

---

## End-to-end flow

```
Browser                WebSocket handler           Voice pipeline              Interview orchestrator
   │                          │                          │                            │
   │──── connect ────────────►│                          │                            │
   │◄─── session.ready ───────│                          │                            │
   │──── session.start ──────►│── start session ────────►│── start / ask question ───►│
   │◄─── interviewer.response │◄─────────────────────────│◄───────────────────────────│
   │◄─── audio.output (xN) ───│◄── TTS stream ───────────│                            │
   │                          │                          │                            │
   │──── audio.input (xN) ───►│── buffer audio ─────────►│                            │
   │──── speech.end ─────────►│── process turn (async) ─►│                            │
   │◄─── transcript.partial ──│◄── STT stream ───────────│                            │
   │◄─── transcript.final ────│                          │── submit_answer ──────────►│
   │◄─── interviewer.thinking ─│                          │── ask_next_question ──────►│
   │◄─── interviewer.response │◄─────────────────────────│◄───────────────────────────│
   │◄─── audio.output (xN) ───│◄── TTS stream ───────────│                            │
   │                          │                          │                            │
   │──── session.end ────────►│── end_session ──────────►│── end_session ────────────►│
   │◄─── session.end ─────────│                          │                            │
```

---

## Architecture notes

### Separation of concerns

| Layer | Responsibility |
|-------|----------------|
| **WebSocket handler** | Connection lifecycle, event validation, routing |
| **Voice pipeline** | Audio buffering, STT/TTS provider calls, event emission |
| **Audio providers** | Replaceable STT/TTS interfaces (`SpeechToTextProvider`, `TextToSpeechProvider`) |
| **Interview orchestrator** | Session state, questions, answers, business rules |

The voice pipeline never embeds LLM prompts. Interviewer reasoning remains in the interviewer agent module invoked by the orchestrator.

### Non-blocking processing

- `speech.end` spawns an asyncio task for turn processing so the WebSocket read loop stays responsive.
- STT and TTS providers use async interfaces; mock providers yield with `asyncio.sleep(0)`.
- TTS audio is streamed as multiple `audio.output` events rather than one blocking payload.

### MVP provider status

| Layer | MVP implementation |
|-------|-------------------|
| Voice STT (mock) | `MockSpeechToTextProvider` in `app/modules/voice/providers/mock.py` |
| Voice STT (OpenAI) | `SpeechToTextAdapter` wrapping `app/ai/providers` STT |
| Voice TTS (mock) | `MockTextToSpeechProvider` in `app/modules/voice/providers/mock.py` |
| Voice TTS (OpenAI) | `TextToSpeechAdapter` wrapping `app/ai/providers` TTS |
| LLM / interviewer | Interviewer agent via interview orchestrator |

Provider selection is controlled by `AI_PROVIDER=mock|openai` and wired in `build_voice_providers()`. Replace providers by implementing the voice-layer protocols (`SpeechToTextProvider`, `TextToSpeechProvider`) or by extending the AI adapter layer; the WebSocket handler and voice pipeline remain unchanged.

---

## Example sequence

```json
→ {"type":"session.start","payload":{"session_id":"…","audio_format":{"sample_rate":16000,"encoding":"pcm_s16le","channels":1}}}

← {"type":"session.ready","payload":{"session_id":"…","status":"configured","question_count":0}}
← {"type":"interviewer.response","payload":{"question_id":"…","text":"Tell me about yourself.","topic_tag":"introduction","should_end_session":false}}
← {"type":"audio.output","payload":{"seq":0,"data":"…","encoding":"pcm_s16le","sample_rate":16000,"is_final":true}}

→ {"type":"audio.input","payload":{"seq":0,"data":"…","timestamp_ms":1000}}
→ {"type":"speech.end","payload":{"timestamp_ms":2500}}

← {"type":"transcript.partial","payload":{"text":"I am a backend engineer","seq":0}}
← {"type":"transcript.final","payload":{"text":"I am a backend engineer with five years of experience.","question_id":"…"}}
← {"type":"interviewer.thinking","payload":{"question_id":"…"}}
← {"type":"interviewer.response","payload":{"question_id":"…","text":"What stack did you use most recently?","topic_tag":"technical","should_end_session":false}}
← {"type":"audio.output","payload":{"seq":0,"data":"…","is_final":true}}
```

---

## Related docs

- [architecture.md](./architecture.md) — system design (§4–8, §17)
- [development.md](./development.md) — local setup
