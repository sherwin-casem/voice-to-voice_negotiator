# Interview Domain

This document describes the core interview lifecycle, orchestration layer, and AI interviewer integration for the Voice-to-Voice Interview Negotiator MVP.

## Overview

The interview domain lives in `apps/api/app/modules/interview/` and exposes REST endpoints under `/api/v1/sessions`. It coordinates:

- **InterviewOrchestrator** — session lifecycle and state transitions (no LLM prompts)
- **InterviewRepository** — PostgreSQL persistence
- **InterviewerAgent** — structured question generation via versioned prompts
- **State machine** — valid status transitions

Evaluation agents are intentionally out of scope for this phase.

## Session States

```
CREATED → CONFIGURED → ACTIVE → COMPLETED
                              ↘ ABANDONED
```

| Status | Meaning |
|--------|---------|
| `created` | Session exists; configuration not yet applied |
| `configured` | Interview type, difficulty, role, context, resume/JD linked |
| `active` | Interview in progress |
| `completed` | Normal end (user, interviewer, or max questions) |
| `abandoned` | Left before completion or ended from configured state |

## Interview Types

Supported values (enum `InterviewType`):

- `behavioral`
- `technical`
- `system_design`
- `leadership`
- `hr`

## Configuration

`SessionConfigInput` captures:

| Field | Description |
|-------|-------------|
| `interview_type` | One of the five types above |
| `difficulty` | `junior`, `mid`, or `senior` |
| `target_role` | e.g. "Senior Backend Engineer" |
| `company_context` | Company stage, culture, domain notes |
| `max_questions` | Optional cap on questions asked |
| `resume_id` | Optional linked resume |
| `job_description_id` | Optional linked job description |

Resume and job description can also be created via `/api/v1/resumes` and `/api/v1/job-descriptions` and attached during configuration.

## REST API Lifecycle

All interview routes require the dev header `X-User-Id: <uuid>` until auth is implemented.

### 1. Create session

`POST /api/v1/sessions`

Creates a session in `created` status.

### 2. Configure session

`PATCH /api/v1/sessions/{session_id}`

Applies interview type, difficulty, target role, company context, resume/JD references. Transitions to `configured`.

### 3. Attach context (optional, before or during setup)

- `POST /api/v1/resumes` — store resume text
- `POST /api/v1/job-descriptions` — store job description text

Reference returned IDs in the configure step.

### 4. Start interview

`POST /api/v1/sessions/{session_id}/start`

Transitions to `active` and returns the first question.

### 5. Answer / next question loop

1. Candidate submits an answer: `POST /api/v1/sessions/{session_id}/answers`
2. Orchestrator validates the question is current and unanswered
3. Request next question: `POST /api/v1/sessions/{session_id}/questions/next`

The orchestrator blocks the next question until the current one is answered.

### 6. End interview

`POST /api/v1/sessions/{session_id}/end`

Explicit end from `active` → `completed`. The session may also end automatically when:

- The interviewer sets `should_end_session` in structured output
- `max_questions` is reached

## Orchestrator Responsibilities

`InterviewOrchestrator` manages deterministic business rules:

- Enforces state machine transitions
- Builds `InterviewerContext` from session config, resume/JD summaries, and prior Q&A
- Persists questions and answers
- Applies post-processing (`normalize_question_output`) to avoid duplicate topic tags
- Ends sessions on user request, interviewer signal, or question cap

It does **not** contain prompt text; prompts live under `app/ai/prompts/interviewer/v1/`.

## Interviewer Agent

`InterviewerAgent` uses:

- **Versioned prompts** — `app/ai/prompts/interviewer/v1/` (`PROMPT_VERSION = "1.0"`)
- **Structured output** — `InterviewerQuestionOutput` schema in `app/ai/schemas/interviewer.py`

The agent considers resume summary, job description, prior turns, asked topics, difficulty, and question number. For local/tests, `AI_PROVIDER=mock` uses `MockInterviewerLLMProvider` with deterministic questions per interview type.

Production path: `InterviewerAgent` calls `StructuredOutputProvider.generate_structured()` with messages from `build_interviewer_messages()`.

## Structured Output Schema

`InterviewerQuestionOutput` fields:

| Field | Purpose |
|-------|---------|
| `question_text` | Next question to ask |
| `topic_tag` | Stable topic identifier (dedup tracking) |
| `follow_up_intent` | Why this follow-up was chosen |
| `is_follow_up` | Whether this probes a prior answer |
| `should_end_session` | Interviewer recommends ending |
| `difficulty_adjustment` | `easier`, `same`, or `harder` |
| `prompt_version` | Prompt version used |

## Testing

| Layer | Location | Type |
|-------|----------|------|
| State machine | `tests/test_state_machine.py` | Unit |
| Validators | `tests/test_validators.py` | Unit |
| Prompt builder | `tests/test_prompt_builder.py` | Unit |
| Orchestrator | `tests/test_orchestrator.py` | Unit (mocked repository) |
| Interviewer agent | `tests/test_interviewer_agent.py` | Mock AI |

Run:

```bash
cd apps/api
uv run pytest
```

## Related Documentation

- [Architecture](./architecture.md)
- [Database schema](./database.md)
- [AI integration](./ai-integration.md)
