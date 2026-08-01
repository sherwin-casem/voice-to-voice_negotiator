# Voice-to-Voice Interview Negotiator — Technical Architecture Proposal

**Status:** Draft  
**Scope:** MVP architecture for a modular monolith  
**Principles:** Production-oriented, replaceable AI providers, no unnecessary microservices

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (Browser)                          │
│  Next.js · React · TypeScript · Tailwind · Web Audio API        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS (REST) + WSS (WebSocket)
┌────────────────────────────▼────────────────────────────────────┐
│                   FastAPI Modular Monolith                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ Identity │ │ Session  │ │Interview │ │Evaluation│         │
│  │  Module  │ │  Module  │ │  Module  │ │  Module  │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │ Context  │ │ Progress │ │Observability│                     │
│  │  Module  │ │  Module  │ │  (cross-cutting)                  │
│  └──────────┘ └──────────┘ └──────────┘                        │
└────────────┬───────────────────────────────┬────────────────────┘
             │                               │
     ┌───────▼───────┐               ┌───────▼───────┐
     │  PostgreSQL   │               │  OpenAI APIs  │
     │  (primary)    │               │ STT·LLM·TTS   │
     └───────────────┘               └───────────────┘
```

**MVP shape:** Single FastAPI process, single Postgres instance, Next.js frontend. Background evaluation runs in-process via async task queue (Python `asyncio` + DB job table) — not a separate microservice.

**Deferred:** Redis, Celery workers, object storage service, CDN, separate eval worker fleet.

---

## 2. Frontend Architecture

```
frontend/
├── app/                    # Next.js App Router
│   ├── (auth)/             # login, register
│   ├── dashboard/          # session history, progress
│   ├── interview/          # live interview UI
│   └── setup/              # resume/JD upload, interview config
├── components/
│   ├── audio/              # mic capture, playback, VAD indicators
│   ├── interview/          # transcript, timer, controls
│   └── evaluation/         # scores, feedback, recommendations
├── hooks/
│   ├── useInterviewSocket.ts
│   └── useAudioStream.ts
├── lib/
│   ├── api-client.ts       # REST wrapper
│   └── ws-client.ts        # typed WebSocket client
└── types/                  # shared TS types (mirrors backend schemas)
```

**Responsibilities:**

- Capture microphone audio (PCM or encoded chunks via `MediaRecorder` / Web Audio API)
- Stream audio to backend over WebSocket
- Play TTS audio returned by backend
- Display live transcript and session state
- Trigger REST calls for setup, history, evaluation retrieval

**State management:** React local state + context for active interview session. No global store needed for MVP. Server state via REST (React Query or SWR recommended).

**Deferred:** Offline support, native mobile apps, whiteboard for system design.

---

## 3. FastAPI Backend Architecture

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── rest/           # REST routers
│   │   └── ws/             # WebSocket handlers
│   ├── modules/
│   │   ├── identity/
│   │   ├── session/
│   │   ├── interviewer/
│   │   ├── context/        # resume/JD
│   │   ├── evaluation/
│   │   └── progress/
│   ├── ai/
│   │   ├── providers/      # OpenAI adapters (STT, LLM, TTS)
│   │   ├── prompts/        # versioned prompt templates
│   │   └── schemas/        # Pydantic models for structured outputs
│   ├── db/
│   │   ├── models/
│   │   └── repositories/
│   └── jobs/               # in-process async eval jobs
```

**Module boundaries:**

| Module | Owns |
|--------|------|
| `identity` | Users, auth tokens, sessions |
| `session` | Interview lifecycle, turns, transcripts, WebSocket state |
| `interviewer` | Question strategy, follow-ups, interview-type plugins |
| `context` | Resume/JD parsing, chunking, retrieval |
| `evaluation` | Multi-agent orchestration, scoring rollup |
| `progress` | Aggregates, trends, recommendations history |

**Cross-cutting:** middleware (auth, request ID, logging), exception handlers, dependency injection.

---

## 4. Real-Time Voice Communication Architecture

**Recommended MVP approach:** Server-orchestrated streaming pipeline over WebSocket.

```
Browser ──audio chunks──► FastAPI WS Handler
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                  VAD/     OpenAI     Session
                turn      Realtime or  State
               detect    STT stream    Store
                    │         │
                    └────┬────┘
                         ▼
                   Interviewer Agent (LLM)
                         │
                         ▼
                   TTS stream ──► Browser playback
```

**Decision (MVP):** Use **OpenAI Realtime API** via backend proxy if latency target is <800ms and turn-taking quality is acceptable. **Fallback/alternative:** chunked STT → LLM → TTS pipeline with explicit turn boundaries.

**Why not WebRTC directly to OpenAI from browser:** Keeps API keys server-side, enables logging, evaluation hooks, and prompt control.

**Deferred:** WebRTC peer connection, custom VAD model, multi-region edge routing.

---

## 5. Audio Streaming Flow

```
1. User grants mic permission
2. Frontend opens WebSocket: ws/interview/{session_id}
3. Frontend sends: session.start
4. Loop while session active:
   a. Capture audio frame (e.g. 100–250ms chunks, 16kHz mono PCM or opus)
   b. Send: audio.chunk { seq, payload_base64, timestamp_ms }
   c. Backend buffers until turn-end signal (silence/VAD or user stop-speaking)
5. Backend responds with:
   - transcript.partial (optional, during user speech)
   - transcript.final (user turn complete)
   - interviewer.audio.chunk (TTS stream)
   - interviewer.text (for UI display)
6. User may send: audio.interrupt (barge-in) → backend cancels in-flight TTS
7. Session ends: session.end → triggers evaluation job
```

**Format:** PCM 16-bit LE, 16kHz mono for STT compatibility (normalize on backend if needed).

---

## 6. Speech-to-Text Flow

```
Audio buffer (user turn)
        │
        ▼
┌───────────────────┐
│ Turn boundary     │  silence ≥ N ms OR client signals speech.end
│ detection         │
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ STT Provider      │  OpenAI Whisper / gpt-4o-transcribe / Realtime STT
│ (streaming or     │
│  batch per turn)  │
└─────────┬─────────┘
          ▼
Transcript segment persisted:
  { turn_id, speaker: "candidate", text, confidence?, start_ms, end_ms }
          │
          ▼
Passed to Interviewer Agent as latest user message
```

**MVP:** Batch STT per completed user turn (simpler, good enough for interview pace).

**Deferred:** Word-level streaming transcript, speaker diarization, accent adaptation.

---

## 7. LLM Reasoning Flow

```
Inputs to Interviewer Agent:
  - system prompt (interview type, persona, rules)
  - session context (resume summary, JD summary, prior turns)
  - conversation history (structured turns)
  - evaluation hints (optional: weak areas from past sessions)

Flow per interviewer turn:
  1. Build prompt from session state + context retrieval
  2. Call LLM with structured output schema:
     { question_text, follow_up_intent, topic_tag, should_end_session }
  3. Persist interviewer turn to DB
  4. Pass question_text to TTS
  5. Emit ws: interviewer.question

Post-session (async):
  Evaluation orchestrator runs specialist agents (see §12–13)
```

**Model tiering (MVP):**

- Interviewer: fast model (low latency, conversational)
- Evaluation agents: stronger reasoning model with structured JSON output
- Scoring/Judge: same or stronger model, consumes all agent outputs

---

## 8. Text-to-Speech Flow

```
Interviewer question text
        │
        ▼
┌───────────────────┐
│ TTS Provider      │  OpenAI TTS (e.g. tts-1 or tts-1-hd)
│ stream=True       │
└─────────┬─────────┘
          ▼
Chunk audio → ws: interviewer.audio.chunk
          │
          ▼
Frontend AudioContext queues and plays chunks sequentially
```

**MVP:** Stream TTS chunks over WebSocket; cache full interviewer audio per turn in DB optional.

**Deferred:** Voice cloning, multi-voice personas, offline TTS.

---

## 9. Interview Session Lifecycle

```
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌────────────┐    ┌──────────┐
│ CREATED │───►│ CONFIGURED│───►│ ACTIVE  │───►│ COMPLETING │───►│ COMPLETED│
└─────────┘    └──────────┘    └─────────┘    └────────────┘    └──────────┘
     │               │              │               │
     │               │              │               └── evaluation job queued
     │               │              └── WS connected, turns exchanged
     │               └── resume/JD attached, type selected
     └── user starts new session

Failure paths:
  ACTIVE ──► ABANDONED (disconnect timeout)
  COMPLETING ──► EVALUATION_FAILED (retryable)
```

**State transitions (server-enforced):**

| From | Event | To |
|------|-------|-----|
| CREATED | configure | CONFIGURED |
| CONFIGURED | start | ACTIVE |
| ACTIVE | end (user or interviewer) | COMPLETING |
| COMPLETING | eval success | COMPLETED |
| ACTIVE | timeout/disconnect | ABANDONED |

---

## 10. Conversation State Management

**Authoritative state lives on the server** (Postgres + in-memory cache for active WS sessions).

```python
SessionState:
  session_id, user_id, status, interview_type
  context: { resume_summary, jd_summary, key_skills[] }
  turns: [ { id, speaker, text, audio_ref?, timestamp } ]
  metadata: { question_count, topics_covered[], started_at, ended_at }
  ws_connection_id (ephemeral, in-memory only)
```

**Turn model:** Strict alternation candidate ↔ interviewer (MVP). Each turn immutable once finalized.

**In-memory vs DB:**

- Active session: in-process dict keyed by `session_id` (MVP; lost on restart → reconnect from DB)
- Persist every finalized turn immediately to Postgres

**Deferred:** CRDT/multi-tab sync, collaborative interviews, replay scrubbing.

---

## 11. Resume and Job Description Processing

```
Upload (PDF/DOCX/TXT) via REST
        │
        ▼
Extract text (pypdf / python-docx / plain)
        │
        ▼
PII scan (basic) + store raw doc encrypted/at rest
        │
        ▼
LLM summarization → structured profile:
  {
    name?, years_experience, skills[], roles[], education[],
    summary_text (≤500 tokens)
  }
        │
        ▼
JD parsing → structured requirements:
  {
    title, level, required_skills[], responsibilities[],
    summary_text (≤300 tokens)
  }
        │
        ▼
Stored in context_documents + linked to session
Injected into Interviewer + Evaluation agent prompts
```

**MVP:** Text paste + PDF upload; one-time parse and cache per document.

**Deferred:** LinkedIn import, semantic chunk retrieval (RAG), multi-JD comparison.

---

## 12. Multi-Agent Evaluation Architecture

Evaluation runs **after session completion** (MVP default). Optional lightweight per-answer signals deferred.

```
                    ┌─────────────────────┐
                    │ Evaluation          │
                    │ Orchestrator        │
                    └──────────┬──────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Interview    │    │ Communication    │    │ Technical        │
│ Analyst      │    │ Evaluation       │    │ Evaluation       │
└──────────────┘    └──────────────────┘    └──────────────────┘
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐    ┌──────────────────┐
│ Behavioral   │    │ Hiring Manager   │
│ Evaluation   │    │ Evaluation       │
└──────────────┘    └──────────────────┘
       │                       │
       └───────────┬───────────┘
                   ▼
         ┌─────────────────┐
         │ Scoring/Judge   │  ← aggregates, resolves conflicts
         └────────┬────────┘
                  ▼
         ┌─────────────────┐
         │ Improvement     │
         │ Coach           │  ← consumes judge output + analyst summary
         └─────────────────┘
```

### Agent Roles

| Agent | Input | Output | Purpose |
|-------|-------|--------|---------|
| **Interviewer Agent** | Session state, context, prior turns | Next question, follow-up intent, end signal | Live interview conductor (runs during ACTIVE session, not post-session eval) |
| **Interview Analyst** | Full transcript, context, interview type | Session summary, key moments, topic coverage, strengths/weaknesses overview | Holistic understanding before specialized scoring |
| **Communication Evaluation** | Transcript + analyst summary | Scores: clarity, structure, conciseness, confidence; evidence quotes | How the candidate communicates |
| **Technical Evaluation** | Transcript + context (JD skills) | Scores: depth, accuracy, problem-solving; per-question notes | Technical/system design merit (skipped or minimal for pure behavioral) |
| **Behavioral Evaluation** | Transcript | STAR adherence, leadership signals, teamwork examples | Behavioral interview rubric |
| **Hiring Manager Evaluation** | All above partial outputs + JD | Hire/no-hire lean, culture fit, role readiness | Simulates hiring decision perspective |
| **Scoring/Judge** | All specialist agent JSON outputs | Unified dimension scores, weighted overall score, confidence | Normalizes scales, resolves contradictions |
| **Improvement Coach** | Judge output + analyst summary + transcript highlights | Prioritized recommendations, practice exercises, example rewrites | Actionable user-facing coaching |

### Interaction Sequence

```
1. Session COMPLETED → Orchestrator loads transcript + context
2. Interview Analyst runs first (provides shared context artifact)
3. Communication, Technical, Behavioral, Hiring Manager run in PARALLEL
   (each receives: transcript, context, analyst_summary)
4. Scoring/Judge runs after all specialists complete (SEQUENTIAL)
5. Improvement Coach runs last (SEQUENTIAL), using judge + analyst output
6. Persist evaluation_result + update progress aggregates
```

---

## 13. Agent Orchestration Strategy

### Options Compared

| Approach | Pros | Cons | MVP fit |
|----------|------|------|---------|
| **A. Sequential chain** | Simple, easy debug | Slow (7+ LLM calls serial), high latency | Poor |
| **B. Parallel specialists + sequential judge/coach** | Good latency/cost balance, clear dependencies | Moderate complexity | **Recommended** |
| **C. Full parallel (incl. judge)** | Fastest | Judge needs all inputs; race conditions; inconsistent | Poor |
| **D. Single mega-prompt** | One API call | Hard to maintain, poor modularity, weak structured output | Poor |
| **E. LangGraph / workflow engine** | Visual, retry policies | Extra dependency, overkill for MVP | Defer |

### MVP Recommendation: Approach B — Parallel specialists, sequential rollup

```python
async def run_evaluation(session_id):
    ctx = load_session_context(session_id)
    analyst = await run_agent("interview_analyst", ctx)

    specialists = await asyncio.gather(
        run_agent("communication_eval", ctx, analyst),
        run_agent("technical_eval", ctx, analyst),
        run_agent("behavioral_eval", ctx, analyst),
        run_agent("hiring_manager_eval", ctx, analyst),
    )

    judge = await run_agent("scoring_judge", ctx, analyst, specialists)
    coach = await run_agent("improvement_coach", ctx, analyst, judge)

    return persist_evaluation(analyst, specialists, judge, coach)
```

**Interview-type gating:** For `behavioral` sessions, Technical Evaluation returns `skipped: true` with null scores. Hiring Manager always runs.

**Deferred:** Per-answer eval pipeline, human-in-the-loop review, custom agent plugins.

---

## 14. Scoring and Evaluation Schema

### Specialist Agent Output (example)

```json
{
  "agent": "communication_evaluation",
  "version": "1.0",
  "dimensions": {
    "clarity": { "score": 7, "max": 10, "evidence": ["..."] },
    "structure": { "score": 6, "max": 10, "evidence": ["..."] },
    "conciseness": { "score": 5, "max": 10, "evidence": ["..."] },
    "confidence": { "score": 8, "max": 10, "evidence": ["..."] }
  },
  "summary": "..."
}
```

### Judge Rollup Output

```json
{
  "overall_score": 72,
  "overall_max": 100,
  "dimension_scores": {
    "communication": 65,
    "technical_knowledge": 70,
    "relevance": 75,
    "structure": 60,
    "confidence": 80,
    "conciseness": 55,
    "problem_solving": 68,
    "behavioral": 72,
    "hire_readiness": 70
  },
  "weights_applied": { "communication": 0.15 },
  "hire_recommendation": "lean_hire",
  "confidence": 0.82,
  "key_strengths": ["..."],
  "key_gaps": ["..."]
}
```

### Coach Output

```json
{
  "priority_recommendations": [
    { "area": "conciseness", "action": "...", "example": "..." }
  ],
  "practice_plan": [
    { "topic": "STAR method", "exercises": ["..."] }
  ]
}
```

**Storage:** `evaluation_runs` (metadata) + `agent_outputs` (JSONB per agent) + `evaluation_summaries` (denormalized for dashboard).

**Weights:** Configurable per `interview_type` in code/config (not user-editable in MVP).

---

## 15. Database Architecture

### Core Tables (MVP)

```
users
  id, email, password_hash, created_at

sessions  (interview sessions)
  id, user_id, status, interview_type, config_json,
  started_at, ended_at, created_at

turns
  id, session_id, speaker, text, sequence_num,
  audio_storage_key?, created_at

context_documents
  id, user_id, doc_type (resume|jd), raw_text,
  parsed_json, created_at

session_context_links
  session_id, context_document_id, role (resume|jd)

evaluation_runs
  id, session_id, status, started_at, completed_at

agent_outputs
  id, evaluation_run_id, agent_name, schema_version, output_json

evaluation_summaries
  id, evaluation_run_id, overall_score, dimension_scores_json,
  hire_recommendation, coach_output_json

progress_snapshots  (materialized per session completion)
  id, user_id, session_id, dimension_scores_json, recorded_at

jobs
  id, job_type, payload_json, status, attempts, created_at
```

**Indexes:** `sessions(user_id, created_at)`, `turns(session_id, sequence_num)`, `evaluation_runs(session_id)`.

**Deferred:** Separate analytics DB, TimescaleDB, full-text search engine, S3 metadata table for audio blobs.

**Audio storage (MVP):** Optional — store turn audio in local filesystem or skip (transcript-only). Defer object storage.

---

## 16. API Design

### REST Endpoints (MVP)

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/me

POST   /api/v1/context/documents          # upload resume/JD
GET    /api/v1/context/documents
GET    /api/v1/context/documents/{id}

POST   /api/v1/sessions                   # create session
PATCH  /api/v1/sessions/{id}              # attach context, set type
POST   /api/v1/sessions/{id}/start
POST   /api/v1/sessions/{id}/end
GET    /api/v1/sessions
GET    /api/v1/sessions/{id}
GET    /api/v1/sessions/{id}/turns

GET    /api/v1/sessions/{id}/evaluation   # poll status + result
GET    /api/v1/progress                   # longitudinal aggregates
GET    /api/v1/progress/trends
```

**Conventions:** JSON request/response, `{ "data": ..., "error": null }` envelope, OpenAPI auto-generated from FastAPI.

**WebSocket:** Separate from REST (see §17).

---

## 17. WebSocket Event Design

**Endpoint:** `WSS /api/v1/ws/interview/{session_id}?token=...`

### Client → Server

| Event | Payload | Description |
|-------|---------|-------------|
| `session.join` | `{ session_id }` | Attach to session |
| `audio.chunk` | `{ seq, data, ts }` | Audio frame |
| `speech.end` | `{ ts }` | User finished speaking |
| `audio.interrupt` | `{}` | Barge-in |
| `session.end` | `{ reason }` | User ends interview |

### Server → Client

| Event | Payload | Description |
|-------|---------|-------------|
| `session.state` | `{ status, turn_count }` | State sync |
| `transcript.partial` | `{ text }` | Interim STT |
| `transcript.final` | `{ turn_id, text, speaker }` | Finalized turn |
| `interviewer.question` | `{ turn_id, text }` | Question text |
| `interviewer.audio.chunk` | `{ seq, data }` | TTS audio |
| `interviewer.audio.end` | `{ turn_id }` | TTS complete |
| `session.ended` | `{ reason }` | Session closed |
| `error` | `{ code, message, recoverable }` | Error |

**Envelope format:**

```json
{ "type": "transcript.final", "payload": { ... }, "request_id": "..." }
```

---

## 18. Authentication Strategy

**MVP:** JWT access token (short-lived) + refresh token (HTTP-only cookie or DB-stored refresh token).

```
Register/Login → access_token (15min) + refresh_token (7d)
REST: Authorization: Bearer {access_token}
WS: token query param or Sec-WebSocket-Protocol (prefer query for MVP simplicity)
```

**Authorization:** User can only access own sessions, documents, evaluations (`user_id` scoping on all queries).

**Deferred:** OAuth (Google/GitHub), MFA, API keys for B2B, RBAC for org accounts.

---

## 19. Error Handling

**Layers:**

1. **Provider errors** (OpenAI timeout, rate limit) → retry with exponential backoff (max 3); map to `PROVIDER_UNAVAILABLE`
2. **Session errors** (invalid state transition) → `409 CONFLICT`, no retry
3. **WS errors** → send `error` event with `recoverable: true/false`; keep session in recoverable state where possible
4. **Evaluation job failure** → mark `EVALUATION_FAILED`, allow manual retry via REST

**Standard error shape (REST):**

```json
{
  "error": {
    "code": "SESSION_NOT_ACTIVE",
    "message": "Cannot send audio when session is not active",
    "request_id": "uuid"
  }
}
```

**Never expose:** API keys, stack traces in production, raw provider responses.

---

## 20. Observability and Logging

**MVP baseline:**

| Concern | Implementation |
|---------|----------------|
| Structured logs | JSON logs with `request_id`, `session_id`, `user_id`, `module` |
| Metrics | Simple counters: sessions_started, eval_duration_ms, llm_tokens, ws_disconnects |
| Tracing | OpenTelemetry optional; at minimum propagate `request_id` WS → LLM calls |
| Cost tracking | Log token usage per agent call; aggregate per session |
| Debug | Prompt/response stored in `agent_outputs` (redact PII in logs) |

**Deferred:** Datadog/Grafana dashboards, alerting, log aggregation service, prompt A/B experiment framework.

---

## 21. Security Considerations

| Area | MVP approach |
|------|--------------|
| Secrets | Environment variables only; never in repo |
| Transport | HTTPS/WSS everywhere in non-local env |
| Input validation | Pydantic at all API boundaries; max upload size for docs |
| Auth | JWT validation on every REST/WS connection |
| Data isolation | Row-level user_id filtering |
| PII | Resume data encrypted at rest (Postgres + app-level or disk encryption); retention policy documented |
| Rate limiting | Basic per-IP/per-user limits on auth and session creation |
| Prompt injection | System prompts instruct agents to ignore candidate attempts to override rubric; transcript labeled as untrusted user content |
| Audio | No long-term audio retention in MVP unless explicitly opted in |

**Deferred:** SOC2 controls, penetration testing, WAF, KMS-managed keys.

---

## 22. Local Development Environment

```
docker-compose.yml:
  - postgres:16
  - (optional) mailhog for auth emails

backend:
  uvicorn app.main:app --reload --port 8000

frontend:
  npm run dev  # port 3000, proxy /api to 8000

.env.example:
  DATABASE_URL, OPENAI_API_KEY, JWT_SECRET, CORS_ORIGINS
```

**Setup flow:**

1. `docker compose up -d`
2. `cd backend && pip install -r requirements.txt && alembic upgrade head`
3. `cd frontend && npm install`
4. Run both services; frontend connects to `ws://localhost:8000/...`

**Deferred:** Dockerized full stack one-command up, seed data scripts, staging environment.

---

## 23. Testing Strategy

| Layer | Scope | Tools |
|-------|-------|-------|
| Unit | Pydantic schemas, scoring rollup, state machine transitions | pytest |
| Integration | REST endpoints, DB repos, eval orchestrator with mocked LLM | pytest + httpx + test Postgres |
| Agent contracts | Each agent output validates against JSON schema | pytest + golden fixtures |
| WS | Session lifecycle events with mocked audio/STT/TTS | pytest-asyncio |
| Frontend | Component tests for evaluation display, WS hook mocking | Vitest + Testing Library |
| E2E | Full interview happy path (smoke) | Playwright (deferred until UI stable) |

**LLM testing:** Mock provider in CI; optional nightly job with real API for prompt regression.

**Deferred:** Load testing, chaos testing, prompt eval benchmarks (RAGAS etc.).

---

## 24. Future Scalability Considerations

| Dimension | MVP | Scale path |
|-----------|-----|------------|
| App server | Single process | Horizontal replicas behind load balancer; sticky sessions for WS |
| Evaluation | In-process async jobs | Celery/ARQ worker pool |
| Database | Single Postgres | Read replicas; partition sessions by date |
| Audio | Transcript-first | S3 + CDN for recordings |
| AI providers | OpenAI only | Provider interface swaps STT/LLM/TTS |
| Multi-tenancy | Single user accounts | Org/workspace model |
| Features | Interview practice | Negotiation mode as new `interview_type` + agents |

**Design hooks now:** `ai/providers/` interface, `interview_type` plugin registry, `agent_name` + `schema_version` on outputs, job table for async work.

---

## MVP Scope vs Deferred Decisions

### Implement Now (MVP)

| Decision | Choice |
|----------|--------|
| Architecture | Modular monolith (Next.js + FastAPI + Postgres) |
| Voice | WebSocket audio streaming; STT per turn; TTS streamed back |
| Interview types | **Behavioral + Technical** (2 types with gating for technical eval) |
| Evaluation timing | **Post-session only** (parallel specialists → judge → coach) |
| Orchestration | asyncio.gather for specialists; sequential judge + coach |
| Auth | Email/password JWT |
| Context | Resume + JD text/PDF upload with LLM summarization |
| Progress | Per-session dimension scores + simple trend endpoint |
| Observability | Structured logs + request_id + token/cost logging |
| Testing | Unit + integration with mocked LLM; agent schema contract tests |

### Defer Until After MVP

| Decision | Rationale |
|----------|-----------|
| Per-answer real-time evaluation | Cost and latency impact on live interview |
| OpenAI Realtime API vs pipeline | Validate via spike; not blocking schema work |
| System design / HR / leadership interview types | Expand plugin registry after core loop works |
| Salary negotiation mode | Separate product surface |
| OAuth / SSO | Email auth sufficient for early users |
| Redis / Celery | In-process jobs adequate at low volume |
| Audio recording storage | Transcript sufficient for eval MVP |
| Object storage (S3) | Local/no audio storage first |
| LangGraph or workflow engine | asyncio orchestration is enough |
| WebRTC | WebSocket pipeline simpler for MVP |
| Advanced RAG for resume/JD | Summarization adequate initially |
| Multi-region / edge | Premature |
| Billing / usage quotas | After product validation |
| Whiteboard for system design | Major frontend scope |
| E2E Playwright suite | After UI stabilizes |

---

## Open Questions for Product Sign-Off

1. Target session length (15 / 30 / 45 min) — affects cost model and question count.
2. Is post-session-only evaluation acceptable UX, or is a "processing…" screen with email notification needed?
3. Should Technical Evaluation run for all sessions or only `interview_type=technical`?
4. Hire/no-hire framing — explicit label or softer "readiness score"?

---

## Recommended Build Order

1. Repo scaffold + Docker Compose + `.env.example`
2. DB schema + migrations + auth module
3. Voice WebSocket spike (STT → interviewer stub → TTS)
4. Interviewer agent loop with session state machine
5. Evaluation orchestrator + agent schemas
6. Frontend: setup → live interview → evaluation dashboard
