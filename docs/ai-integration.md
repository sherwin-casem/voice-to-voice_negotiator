# AI Integration Layer

Modular AI provider abstractions for the Voice-to-Voice Interview Negotiator API.

Business logic and future interview/evaluation agents should depend on these provider interfaces — not on the OpenAI SDK directly.

## Goals

- Replaceable AI providers (mock for tests/local, OpenAI for production)
- Configurable models via environment variables
- Safe error handling without exposing API keys
- Structured logging, timeouts, and retries for transient failures

## Architecture

```
app/ai/
├── types.py                 Shared request/response dataclasses
├── errors.py                Provider error hierarchy
├── logging.py               Structured AI log helpers
├── retry.py                 Retry wrapper for retryable failures
├── providers/
│   ├── base.py              Protocol definitions
│   ├── factory.py           build_ai_providers()
│   ├── mock.py              Deterministic mock providers
│   └── openai/              OpenAI SDK implementation (isolated)
│       ├── _client.py       Client factory + error mapping
│       ├── llm.py           Text, structured, streaming
│       ├── stt.py           Speech-to-text
│       └── tts.py           Text-to-speech
```

## Provider interfaces

| Interface | Purpose |
|-----------|---------|
| `TextGenerationProvider` | Single-shot text generation / reasoning |
| `StructuredOutputProvider` | Pydantic-validated JSON outputs |
| `StreamingTextProvider` | Token/chunk streaming text responses |
| `SpeechToTextProvider` | Audio transcription |
| `TextToSpeechProvider` | Speech synthesis streaming |

Use the factory:

```python
from app.ai.providers.factory import get_ai_providers

providers = get_ai_providers()
result = await providers.text.generate_text(messages)
parsed = await providers.structured.generate_structured(messages, MySchema)
```

`LLMProvider` remains a backward-compatible alias for `StructuredOutputProvider`.

## Configuration

Set in root `.env` (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PROVIDER` | `mock` | `mock` or `openai` |
| `OPENAI_API_KEY` | — | Required when `AI_PROVIDER=openai` |
| `OPENAI_ORGANIZATION` | — | Optional org ID |
| `OPENAI_BASE_URL` | — | Optional custom API base URL |
| `OPENAI_LLM_MODEL` | `gpt-4o-mini` | Text generation model |
| `OPENAI_STRUCTURED_MODEL` | `gpt-4o-mini` | Structured output model |
| `OPENAI_STREAMING_MODEL` | `gpt-4o-mini` | Streaming text model |
| `OPENAI_STT_MODEL` | `gpt-4o-transcribe` | Speech-to-text model |
| `OPENAI_TTS_MODEL` | `tts-1` | Text-to-speech model |
| `OPENAI_TTS_VOICE` | `alloy` | Default TTS voice |
| `AI_REQUEST_TIMEOUT_SECONDS` | `60` | Provider request timeout |
| `AI_MAX_RETRIES` | `2` | Retries for retryable errors |
| `AI_RETRY_BACKOFF_SECONDS` | `0.5` | Initial retry backoff |

## Error handling

All provider failures are mapped to `AIProviderError` subclasses/codes:

- `AI_AUTHENTICATION_ERROR` — invalid/missing credentials (not retryable)
- `AI_RATE_LIMIT` — retryable
- `AI_TIMEOUT` — retryable
- `AI_CONNECTION_ERROR` — retryable
- `AI_UNAVAILABLE` — retryable upstream 5xx
- `AI_RESPONSE_ERROR` — non-retryable response issues

Logs include `component=ai`, `operation`, `provider`, and `model`. API keys are never logged.

## Testing

Unit tests live in `apps/api/tests/ai/` and use mocks — no real OpenAI calls:

```bash
uv run --directory apps/api pytest tests/ai -q
```

## Usage guidelines

1. Inject providers via `build_ai_providers()` or FastAPI dependencies (future).
2. Keep prompts in `app/ai/prompts/` and schemas in `app/ai/schemas/`.
3. Do not import `openai` outside `app/ai/providers/openai/`.
4. Interview/evaluation agents should consume provider interfaces only.
