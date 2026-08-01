# PostgreSQL Database Schema — MVP

**Status:** Design (not yet implemented)  
**Database:** PostgreSQL 16+  
**Aligns with:** [architecture.md](./architecture.md), [Agents.md](../Agents.md)

This document defines the MVP relational schema. It supports voice interview sessions, resume/JD context, multi-agent evaluation at **session** and **answer** scope, queryable scores, and longitudinal progress tracking.

---

## Design Principles

1. **UUID primary keys** everywhere (`gen_random_uuid()` via `pgcrypto` extension).
2. **`created_at` / `updated_at`** on mutable entities; immutable event rows may omit `updated_at`.
3. **Relational columns** for entities you join, filter, sort, and enforce integrity on.
4. **JSONB** for agent payloads, parsed document structures, and evidence blobs that evolve with prompt versions.
5. **No premature normalization** — denormalize rollups (`evaluation_results`, `user_progress_snapshots`) for read-heavy dashboards.
6. **Multiple agents, same target** — `agent_evaluations` holds one row per agent per `evaluation_run`; agents never overwrite each other.
7. **Per-answer and session eval** — `evaluation_runs.scope` + nullable `answer_id` distinguish scope without duplicating tables.

---

## Entity Relationship Overview

```
users ──1:1── user_profiles
  │
  ├──1:N── resumes
  ├──1:N── job_descriptions
  ├──1:N── interview_configurations
  │
  └──1:N── interview_sessions ──N:1── interview_configurations
                │                      ──N:1── resumes (optional)
                │                      ──N:1── job_descriptions (optional)
                │
                ├──1:N── interview_questions ──1:1── candidate_answers (MVP)
                ├──1:N── transcript_segments
                ├──1:1── session_transcripts
                │
                └──1:N── evaluation_runs ──0:1── candidate_answers (when scope=answer)
                              │
                              ├──1:N── agent_evaluations ──1:N── evaluation_scores
                              ├──1:1── evaluation_results
                              └──1:N── improvement_recommendations

users ──1:N── user_progress_snapshots ──N:1── interview_sessions
                                              ──N:1── evaluation_runs
```

---

## PostgreSQL Extensions & Conventions

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- gen_random_uuid()

-- Shared trigger function for updated_at (apply in migrations)
-- CREATE OR REPLACE FUNCTION set_updated_at() ...
```

**Naming:** `snake_case` tables and columns. Enum types prefixed with domain (`interview_session_status`).

**Timestamps:** `TIMESTAMPTZ NOT NULL DEFAULT now()` for all `created_at` / `updated_at`.

**Soft delete:** Not used in MVP. Use `status` columns where lifecycle matters.

---

## Enumerations

```sql
CREATE TYPE interview_type AS ENUM (
  'behavioral',
  'technical',
  'system_design',
  'hr',
  'leadership'
);

CREATE TYPE interview_session_status AS ENUM (
  'created',
  'configured',
  'active',
  'completing',
  'completed',
  'abandoned',
  'evaluation_failed'
);

CREATE TYPE evaluation_scope AS ENUM (
  'session',
  'answer'
);

CREATE TYPE evaluation_run_status AS ENUM (
  'pending',
  'running',
  'completed',
  'failed',
  'skipped'
);

CREATE TYPE agent_name AS ENUM (
  'interviewer',              -- live only; not stored in agent_evaluations post-session
  'interview_analyst',
  'communication_evaluation',
  'technical_evaluation',
  'behavioral_evaluation',
  'hiring_manager_evaluation',
  'scoring_judge',
  'improvement_coach'
);

CREATE TYPE speaker_role AS ENUM (
  'interviewer',
  'candidate'
);

CREATE TYPE document_parse_status AS ENUM (
  'pending',
  'parsed',
  'failed'
);

CREATE TYPE hire_recommendation AS ENUM (
  'strong_hire',
  'lean_hire',
  'neutral',
  'lean_no_hire',
  'no_hire'
);
```

**MVP note:** Only `behavioral` and `technical` interview types are active at launch; other enum values are reserved.

---

## Table Definitions

### 1. `users`

Authentication identity. Profile data lives in `user_profiles`.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `email` | `VARCHAR(320) UNIQUE NOT NULL` | Normalized lowercase |
| `password_hash` | `VARCHAR(255) NOT NULL` | bcrypt/argon2 |
| `is_active` | `BOOLEAN NOT NULL DEFAULT true` | |
| `email_verified_at` | `TIMESTAMPTZ` | Nullable |
| `last_login_at` | `TIMESTAMPTZ` | Nullable |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:** All relational — queried for auth and account management.

**Indexes:** `UNIQUE (email)`, `(is_active)` partial where needed.

---

### 2. `user_profiles`

Extended user information and preferences.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `user_id` | `UUID UNIQUE NOT NULL FK → users(id) ON DELETE CASCADE` | 1:1 |
| `display_name` | `VARCHAR(120)` | |
| `target_role` | `VARCHAR(200)` | e.g. "Senior Backend Engineer" |
| `experience_level` | `VARCHAR(50)` | e.g. "mid", "senior" |
| `timezone` | `VARCHAR(64)` | IANA timezone |
| `preferences` | `JSONB NOT NULL DEFAULT '{}'` | UI prefs, notification settings |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:**

| Relational | JSONB |
|------------|-------|
| `display_name`, `target_role`, `experience_level`, `timezone` | `preferences` — infrequent queries, shape may evolve |

---

### 3. `refresh_tokens`

JWT refresh token storage (optional but recommended for revocation).

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `user_id` | `UUID NOT NULL FK → users(id) ON DELETE CASCADE` | |
| `token_hash` | `VARCHAR(255) NOT NULL` | Store hash, not raw token |
| `expires_at` | `TIMESTAMPTZ NOT NULL` | |
| `revoked_at` | `TIMESTAMPTZ` | |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |

**Indexes:** `(user_id)`, `(token_hash)` where `revoked_at IS NULL`.

---

### 4. `resumes`

User-uploaded resumes with parsed structured content.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `user_id` | `UUID NOT NULL FK → users(id) ON DELETE CASCADE` | |
| `title` | `VARCHAR(200) NOT NULL` | User label, e.g. "2026 SWE Resume" |
| `source_filename` | `VARCHAR(500)` | Original upload name |
| `mime_type` | `VARCHAR(100)` | |
| `raw_text` | `TEXT NOT NULL` | Extracted plain text |
| `parse_status` | `document_parse_status NOT NULL DEFAULT 'pending'` | |
| `parsed_profile` | `JSONB` | Structured LLM parse (skills, roles, education) |
| `summary_text` | `TEXT` | Short summary for prompt injection (≤500 tokens) |
| `is_default` | `BOOLEAN NOT NULL DEFAULT false` | One default per user (app-enforced) |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:**

| Relational | JSONB |
|------------|-------|
| `title`, `parse_status`, `summary_text`, `is_default` | `parsed_profile` — nested skills/roles; query via `@>` / GIN index if needed later |

**Indexes:** `(user_id, created_at DESC)`, GIN on `parsed_profile` (optional, defer until needed).

---

### 5. `job_descriptions`

User-provided job descriptions, structurally parallel to resumes.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `user_id` | `UUID NOT NULL FK → users(id) ON DELETE CASCADE` | |
| `title` | `VARCHAR(200) NOT NULL` | e.g. "Stripe Backend JD" |
| `company_name` | `VARCHAR(200)` | |
| `source_filename` | `VARCHAR(500)` | |
| `mime_type` | `VARCHAR(100)` | |
| `raw_text` | `TEXT NOT NULL` | |
| `parse_status` | `document_parse_status NOT NULL DEFAULT 'pending'` | |
| `parsed_requirements` | `JSONB` | title, level, required_skills, responsibilities |
| `summary_text` | `TEXT` | Short summary for prompts (≤300 tokens) |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:** Same pattern as `resumes`.

**Indexes:** `(user_id, created_at DESC)`.

---

### 6. `interview_configurations`

Reusable interview setup. Snapshotted onto sessions so historical sessions remain interpretable if config changes.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `user_id` | `UUID NOT NULL FK → users(id) ON DELETE CASCADE` | |
| `name` | `VARCHAR(200) NOT NULL` | e.g. "30-min Technical Mock" |
| `interview_type` | `interview_type NOT NULL` | |
| `target_duration_minutes` | `INTEGER` | 15, 30, 45 |
| `max_questions` | `INTEGER` | Optional cap |
| `difficulty` | `VARCHAR(50)` | e.g. "mid", "senior" |
| `settings` | `JSONB NOT NULL DEFAULT '{}'` | Eval weights override, focus areas, language |
| `is_template` | `BOOLEAN NOT NULL DEFAULT true` | User-saved template vs one-off |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:**

| Relational | JSONB |
|------------|-------|
| `interview_type`, `target_duration_minutes`, `max_questions`, `difficulty` | `settings` — extensible config without migrations |

**Indexes:** `(user_id, created_at DESC)`.

---

### 7. `interview_sessions`

Core interview instance and lifecycle state machine.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `user_id` | `UUID NOT NULL FK → users(id) ON DELETE CASCADE` | |
| `configuration_id` | `UUID FK → interview_configurations(id) ON DELETE SET NULL` | Source template |
| `resume_id` | `UUID FK → resumes(id) ON DELETE SET NULL` | |
| `job_description_id` | `UUID FK → job_descriptions(id) ON DELETE SET NULL` | |
| `status` | `interview_session_status NOT NULL DEFAULT 'created'` | |
| `interview_type` | `interview_type NOT NULL` | Copied from config at configure time |
| `title` | `VARCHAR(200)` | Optional display title |
| `config_snapshot` | `JSONB NOT NULL DEFAULT '{}'` | Frozen copy of config + context summaries at start |
| `question_count` | `INTEGER NOT NULL DEFAULT 0` | Denormalized counter |
| `started_at` | `TIMESTAMPTZ` | |
| `ended_at` | `TIMESTAMPTZ` | |
| `end_reason` | `VARCHAR(100)` | user_ended, interviewer_ended, timeout, error |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:**

| Relational | JSONB |
|------------|-------|
| `status`, `interview_type`, FKs, timestamps, `question_count` | `config_snapshot` — immutable point-in-time context for eval reproducibility |

**Indexes:**

- `(user_id, created_at DESC)`
- `(user_id, status)`
- `(status)` where active sessions queried globally (admin/debug)

---

### 8. `interview_questions`

Each interviewer question in a session. Generated dynamically by the Interviewer Agent.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `session_id` | `UUID NOT NULL FK → interview_sessions(id) ON DELETE CASCADE` | |
| `sequence_num` | `INTEGER NOT NULL` | 1-based order within session |
| `question_text` | `TEXT NOT NULL` | Spoken/displayed question |
| `topic_tag` | `VARCHAR(100)` | e.g. "leadership", "system_design" |
| `follow_up_intent` | `VARCHAR(200)` | Why this question was asked |
| `is_follow_up` | `BOOLEAN NOT NULL DEFAULT false` | |
| `parent_question_id` | `UUID FK → interview_questions(id) ON DELETE SET NULL` | Follow-up chain |
| `agent_metadata` | `JSONB NOT NULL DEFAULT '{}'` | LLM structured output extras |
| `asked_at` | `TIMESTAMPTZ NOT NULL` | |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:**

| Relational | JSONB |
|------------|-------|
| `sequence_num`, `question_text`, `topic_tag`, `follow_up_intent`, `is_follow_up` | `agent_metadata` — model version, prompt id, `should_end_session` flag |

**Constraints:** `UNIQUE (session_id, sequence_num)`.

**Indexes:** `(session_id, sequence_num)`.

---

### 9. `candidate_answers`

Candidate response to a question. Primary artifact for per-answer evaluation.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `session_id` | `UUID NOT NULL FK → interview_sessions(id) ON DELETE CASCADE` | Denormalized for query convenience |
| `question_id` | `UUID NOT NULL FK → interview_questions(id) ON DELETE CASCADE` | |
| `answer_text` | `TEXT NOT NULL` | Final STT transcript of answer |
| `duration_ms` | `INTEGER` | Speaking duration |
| `stt_confidence` | `NUMERIC(5,4)` | Optional 0–1 |
| `audio_storage_key` | `VARCHAR(500)` | Optional file/object key |
| `word_count` | `INTEGER` | Denormalized |
| `answered_at` | `TIMESTAMPTZ NOT NULL` | |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:** All core fields relational — filtered and displayed in UI. No JSONB on answers in MVP.

**Constraints:** `UNIQUE (question_id)` — one answer per question in MVP.

**Indexes:** `(session_id, answered_at)`, `(question_id)`.

---

### 10. `transcript_segments`

Granular STT segments during live session. Supports partial transcripts and audit trail.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `session_id` | `UUID NOT NULL FK → interview_sessions(id) ON DELETE CASCADE` | |
| `question_id` | `UUID FK → interview_questions(id) ON DELETE SET NULL` | |
| `answer_id` | `UUID FK → candidate_answers(id) ON DELETE SET NULL` | |
| `speaker` | `speaker_role NOT NULL` | |
| `sequence_num` | `INTEGER NOT NULL` | Order within session |
| `text` | `TEXT NOT NULL` | |
| `is_final` | `BOOLEAN NOT NULL DEFAULT false` | Partial vs finalized STT |
| `start_ms` | `INTEGER` | Offset from session start |
| `end_ms` | `INTEGER` | |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:** All relational. Segments are append-only events.

**Indexes:** `(session_id, sequence_num)`, `(answer_id)` where `is_final = true`.

---

### 11. `session_transcripts`

Assembled full-session transcript for evaluation input. Built when session ends.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `session_id` | `UUID UNIQUE NOT NULL FK → interview_sessions(id) ON DELETE CASCADE` | 1:1 |
| `full_text` | `TEXT NOT NULL` | Q&A formatted conversation |
| `structured_transcript` | `JSONB NOT NULL DEFAULT '[]'` | Array of `{ speaker, text, question_id?, answer_id?, sequence }` |
| `word_count` | `INTEGER NOT NULL DEFAULT 0` | |
| `generated_at` | `TIMESTAMPTZ NOT NULL` | |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:**

| Relational | JSONB |
|------------|-------|
| `full_text`, `word_count` — full-text search later | `structured_transcript` — preserves turn linkage for agents |

**Indexes:** `(session_id)`. Consider `GIN` on `to_tsvector('english', full_text)` post-MVP.

---

### 12. `evaluation_runs`

Orchestration unit for one evaluation pipeline execution. Supports **session** and **answer** scope.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `session_id` | `UUID NOT NULL FK → interview_sessions(id) ON DELETE CASCADE` | |
| `answer_id` | `UUID FK → candidate_answers(id) ON DELETE CASCADE` | **NULL when scope = session** |
| `scope` | `evaluation_scope NOT NULL` | `session` or `answer` |
| `status` | `evaluation_run_status NOT NULL DEFAULT 'pending'` | |
| `trigger` | `VARCHAR(50) NOT NULL` | e.g. `session_completed`, `answer_submitted` |
| `orchestration_version` | `VARCHAR(20) NOT NULL DEFAULT '1.0'` | Pipeline version |
| `error_message` | `TEXT` | On failure |
| `started_at` | `TIMESTAMPTZ` | |
| `completed_at` | `TIMESTAMPTZ` | |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | |

**Scope rules:**

- `scope = 'session'` → `answer_id IS NULL`. Runs full multi-agent pipeline (analyst → specialists → judge → coach).
- `scope = 'answer'` → `answer_id IS NOT NULL`. Runs lightweight or subset agents (e.g. communication + technical only). MVP may defer per-answer runs but schema supports them.

**Constraints:**

```sql
CHECK (
  (scope = 'session' AND answer_id IS NULL) OR
  (scope = 'answer' AND answer_id IS NOT NULL)
)
```

**Indexes:** `(session_id, scope)`, `(answer_id)` where not null, `(status)` for job polling.

---

### 13. `agent_evaluations`

One row per AI agent per evaluation run. Agents evaluate independently without overwriting peers.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `evaluation_run_id` | `UUID NOT NULL FK → evaluation_runs(id) ON DELETE CASCADE` | |
| `agent_name` | `agent_name NOT NULL` | |
| `schema_version` | `VARCHAR(20) NOT NULL` | e.g. `1.0` |
| `status` | `evaluation_run_status NOT NULL DEFAULT 'pending'` | |
| `skipped` | `BOOLEAN NOT NULL DEFAULT false` | e.g. technical eval on behavioral session |
| `skip_reason` | `VARCHAR(200)` | |
| `model_id` | `VARCHAR(100)` | e.g. `gpt-4o` |
| `prompt_version` | `VARCHAR(50)` | |
| `summary` | `TEXT` | Agent narrative summary |
| `output` | `JSONB NOT NULL DEFAULT '{}'` | Full structured agent response |
| `token_usage` | `JSONB` | `{ prompt_tokens, completion_tokens }` |
| `latency_ms` | `INTEGER` | |
| `started_at` | `TIMESTAMPTZ` | |
| `completed_at` | `TIMESTAMPTZ` | |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:**

| Relational | JSONB |
|------------|-------|
| `agent_name`, `status`, `skipped`, `summary`, timing, model metadata | `output` — complete agent payload; `token_usage` |

**Constraints:** `UNIQUE (evaluation_run_id, agent_name)` — one evaluation per agent per run.

**Indexes:** `(evaluation_run_id)`, `(agent_name, created_at DESC)` for analytics.

**Multiple agents, same answer:** When three agents evaluate answer X, there is one `evaluation_run` (scope=`answer`, `answer_id=X`) with three `agent_evaluations` rows — one per agent.

---

### 14. `evaluation_scores`

Normalized, queryable dimension scores extracted from agent outputs. Enables SQL aggregation and progress trends.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `agent_evaluation_id` | `UUID NOT NULL FK → agent_evaluations(id) ON DELETE CASCADE` | |
| `evaluation_run_id` | `UUID NOT NULL FK → evaluation_runs(id) ON DELETE CASCADE` | Denormalized for session-level queries |
| `session_id` | `UUID NOT NULL FK → interview_sessions(id) ON DELETE CASCADE` | Denormalized |
| `answer_id` | `UUID FK → candidate_answers(id) ON DELETE CASCADE` | Set when scope=answer |
| `agent_name` | `agent_name NOT NULL` | Denormalized |
| `dimension_key` | `VARCHAR(80) NOT NULL` | e.g. `clarity`, `technical_knowledge` |
| `score` | `NUMERIC(6,2) NOT NULL` | Normalized 0–100 or raw scale |
| `max_score` | `NUMERIC(6,2) NOT NULL DEFAULT 100` | |
| `normalized_score` | `NUMERIC(6,2) GENERATED ALWAYS AS (score / NULLIF(max_score, 0) * 100) STORED` | 0–100 |
| `weight` | `NUMERIC(5,4)` | Weight used by judge (nullable until rollup) |
| `evidence` | `JSONB NOT NULL DEFAULT '[]'` | Quote snippets supporting score |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:**

| Relational | JSONB |
|------------|-------|
| `dimension_key`, `score`, `max_score`, `normalized_score`, FKs — **primary query surface** | `evidence` — variable-length quote arrays |

**Constraints:** `UNIQUE (agent_evaluation_id, dimension_key)`.

**Indexes:**

- `(session_id, dimension_key, created_at DESC)` — progress trends
- `(answer_id, dimension_key)` — per-answer drill-down
- `(evaluation_run_id)`
- `(agent_name, dimension_key)`

**Example query — average communication clarity across sessions:**

```sql
SELECT AVG(es.normalized_score)
FROM evaluation_scores es
JOIN interview_sessions s ON s.id = es.session_id
WHERE s.user_id = :user_id
  AND es.dimension_key = 'clarity'
  AND es.agent_name = 'communication_evaluation';
```

---

### 15. `evaluation_results`

Rollup produced by the Scoring/Judge agent (and denormalized for fast reads). One per completed session-scoped run; optional for answer-scoped runs.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `evaluation_run_id` | `UUID UNIQUE NOT NULL FK → evaluation_runs(id) ON DELETE CASCADE` | 1:1 with run |
| `session_id` | `UUID NOT NULL FK → interview_sessions(id) ON DELETE CASCADE` | |
| `answer_id` | `UUID FK → candidate_answers(id) ON DELETE CASCADE` | When answer-scoped rollup |
| `overall_score` | `NUMERIC(6,2) NOT NULL` | 0–100 |
| `overall_max` | `NUMERIC(6,2) NOT NULL DEFAULT 100` | |
| `hire_recommendation` | `hire_recommendation` | Session-level primarily |
| `confidence` | `NUMERIC(5,4)` | Judge confidence 0–1 |
| `dimension_scores` | `JSONB NOT NULL DEFAULT '{}'` | Unified rollup `{ communication: 65, ... }` |
| `weights_applied` | `JSONB NOT NULL DEFAULT '{}'` | |
| `key_strengths` | `JSONB NOT NULL DEFAULT '[]'` | |
| `key_gaps` | `JSONB NOT NULL DEFAULT '[]'` | |
| `judge_output` | `JSONB NOT NULL DEFAULT '{}'` | Full judge payload archive |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:**

| Relational | JSONB |
|------------|-------|
| `overall_score`, `hire_recommendation`, `confidence` — dashboard filters/sorts | `dimension_scores`, `key_strengths`, `key_gaps`, `judge_output` |

**Why both `evaluation_scores` and `dimension_scores` JSONB?**

- `evaluation_scores` — granular, per-agent, queryable rows for analytics.
- `evaluation_results.dimension_scores` — judge-normalized rollup for single-read API responses.

**Indexes:** `(session_id, created_at DESC)`, `(overall_score)`.

---

### 16. `improvement_recommendations`

Actionable coaching output from the Improvement Coach agent. Normalized rows for listing, filtering, and tracking completion.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `evaluation_run_id` | `UUID NOT NULL FK → evaluation_runs(id) ON DELETE CASCADE` | |
| `agent_evaluation_id` | `UUID FK → agent_evaluations(id) ON DELETE SET NULL` | Coach agent row |
| `session_id` | `UUID NOT NULL FK → interview_sessions(id) ON DELETE CASCADE` | |
| `answer_id` | `UUID FK → candidate_answers(id) ON DELETE SET NULL` | Linked answer if applicable |
| `priority` | `INTEGER NOT NULL DEFAULT 1` | 1 = highest |
| `area` | `VARCHAR(80) NOT NULL` | e.g. `conciseness`, `STAR_method` |
| `recommendation_text` | `TEXT NOT NULL` | |
| `example_text` | `TEXT` | Suggested rewrite or example |
| `action_items` | `JSONB NOT NULL DEFAULT '[]'` | `[ { "task": "...", "resource": "..." } ]` |
| `practice_plan` | `JSONB` | Exercises from coach |
| `is_acknowledged` | `BOOLEAN NOT NULL DEFAULT false` | User marked as read/done |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:**

| Relational | JSONB |
|------------|-------|
| `priority`, `area`, `recommendation_text`, `is_acknowledged` | `action_items`, `practice_plan` |

**Indexes:** `(session_id, priority)`, `(session_id, area)`.

---

### 17. `user_progress_snapshots`

Longitudinal progress captured after each completed session evaluation. Powers trend charts.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `user_id` | `UUID NOT NULL FK → users(id) ON DELETE CASCADE` | |
| `session_id` | `UUID NOT NULL FK → interview_sessions(id) ON DELETE CASCADE` | |
| `evaluation_run_id` | `UUID NOT NULL FK → evaluation_runs(id) ON DELETE CASCADE` | Source session eval |
| `interview_type` | `interview_type NOT NULL` | |
| `overall_score` | `NUMERIC(6,2) NOT NULL` | |
| `dimension_scores` | `JSONB NOT NULL DEFAULT '{}'` | Snapshot of judge rollup |
| `sessions_completed_count` | `INTEGER NOT NULL` | Running total at snapshot time |
| `recorded_at` | `TIMESTAMPTZ NOT NULL` | |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |

**Relational vs JSONB:**

| Relational | JSONB |
|------------|-------|
| `overall_score`, `interview_type`, `sessions_completed_count`, timestamps | `dimension_scores` — multi-dimensional trend data |

**Indexes:** `(user_id, recorded_at DESC)`, `(user_id, interview_type, recorded_at DESC)`.

**Population:** Insert one row when a session-scoped `evaluation_run` completes successfully.

---

### 18. `background_jobs`

Async job queue for evaluation orchestration (in-process worker polls this table in MVP).

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID PK` | |
| `job_type` | `VARCHAR(80) NOT NULL` | e.g. `run_session_evaluation` |
| `payload` | `JSONB NOT NULL DEFAULT '{}'` | `{ evaluation_run_id, session_id }` |
| `status` | `VARCHAR(20) NOT NULL DEFAULT 'pending'` | pending, running, completed, failed |
| `attempts` | `INTEGER NOT NULL DEFAULT 0` | |
| `max_attempts` | `INTEGER NOT NULL DEFAULT 3` | |
| `run_after` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |
| `locked_at` | `TIMESTAMPTZ` | Worker lock |
| `locked_by` | `VARCHAR(100)` | Worker id |
| `error_message` | `TEXT` | |
| `created_at` | `TIMESTAMPTZ NOT NULL` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | |

**Indexes:** `(status, run_after)` where `status = 'pending'`.

---

## Evaluation Data Flow

### Session-scoped evaluation (primary MVP path)

```
interview_session (completed)
        │
        ▼
evaluation_runs (scope=session, answer_id=NULL)
        │
        ├── agent_evaluations (interview_analyst)
        ├── agent_evaluations (communication_evaluation)  ──► evaluation_scores
        ├── agent_evaluations (technical_evaluation)       ──► evaluation_scores
        ├── agent_evaluations (behavioral_evaluation)      ──► evaluation_scores
        ├── agent_evaluations (hiring_manager_evaluation)  ──► evaluation_scores
        ├── agent_evaluations (scoring_judge)              ──► evaluation_results
        └── agent_evaluations (improvement_coach)          ──► improvement_recommendations
                                        │
                                        ▼
                              user_progress_snapshots
```

### Answer-scoped evaluation (supported in schema; optional in MVP launch)

```
candidate_answer (submitted)
        │
        ▼
evaluation_runs (scope=answer, answer_id=<id>)
        │
        ├── agent_evaluations (communication_evaluation)  ──► evaluation_scores (answer_id set)
        ├── agent_evaluations (technical_evaluation)       ──► evaluation_scores
        └── agent_evaluations (scoring_judge)              ──► evaluation_results (optional mini-rollup)
```

Each agent writes its own `agent_evaluations` row and its own `evaluation_scores` rows. The Judge reads all agent `output` JSONB and writes `evaluation_results` plus consolidated dimension rows if desired.

---

## Relational vs JSONB — Decision Guide

| Use relational columns when… | Use JSONB when… |
|------------------------------|-----------------|
| Filtering, sorting, joining in SQL | Schema evolves with prompt/agent versions |
| Enforcing FK integrity | Storing full LLM structured output archive |
| Aggregating (AVG, COUNT, GROUP BY) | Nested arrays (evidence quotes, action items) |
| Values have stable meaning across releases | Field set differs per agent type |
| Indexed lookup performance matters | Rarely queried fields; display-only blobs |

**Rule of thumb for this project:** Extract scores you chart or trend (`evaluation_scores`) relationally; archive agent creativity (`agent_evaluations.output`) in JSONB.

---

## Key Indexes Summary

| Table | Index | Purpose |
|-------|-------|---------|
| `interview_sessions` | `(user_id, created_at DESC)` | Session history |
| `interview_questions` | `(session_id, sequence_num)` | Ordered Q&A |
| `candidate_answers` | `(session_id, answered_at)` | Answer timeline |
| `evaluation_runs` | `(session_id, scope)` | Find session/answer evals |
| `agent_evaluations` | `UNIQUE (evaluation_run_id, agent_name)` | Idempotent agent writes |
| `evaluation_scores` | `(session_id, dimension_key, created_at DESC)` | Progress analytics |
| `evaluation_results` | `(session_id, created_at DESC)` | Latest session score |
| `user_progress_snapshots` | `(user_id, recorded_at DESC)` | Trend charts |
| `background_jobs` | `(status, run_after)` | Job polling |

---

## Mapping to Product Concepts

| Product concept | Primary table(s) |
|-----------------|------------------|
| Users | `users`, `refresh_tokens` |
| User profiles | `user_profiles` |
| Resumes | `resumes` |
| Job descriptions | `job_descriptions` |
| Interview sessions | `interview_sessions` |
| Interview configurations | `interview_configurations`, `interview_sessions.config_snapshot` |
| Interview questions | `interview_questions` |
| Candidate answers | `candidate_answers` |
| Transcripts | `transcript_segments`, `session_transcripts` |
| Evaluation results | `evaluation_results`, `evaluation_runs` |
| Agent evaluations | `agent_evaluations` |
| Scores | `evaluation_scores`, `evaluation_results.overall_score` |
| Improvement recommendations | `improvement_recommendations` |
| User progress over time | `user_progress_snapshots`, query `evaluation_scores` |

---

## MVP Implementation vs Deferred

| Implement in first migration | Defer |
|-------------------------------|-------|
| All tables above | Full-text search indexes on transcripts |
| Session-scoped evaluation path | Per-answer eval job triggers (schema ready) |
| `evaluation_scores` extraction | Materialized views for analytics |
| `user_progress_snapshots` on session complete | Partitioning large tables by date |
| Basic indexes listed above | Row-level security policies (use app-level scoping first) |
| Enum types | Separate read replica |

---

## Assumptions

1. **One answer per question** in MVP (`UNIQUE (question_id)` on `candidate_answers`).
2. **Session transcript** is assembled once at session end into `session_transcripts`.
3. **Per-answer evaluation** is schema-supported but may not be triggered at MVP launch (post-session eval is primary per architecture).
4. **Interviewer Agent** output is stored in `interview_questions`, not `agent_evaluations` (live conductor, not post-session evaluator).
5. **Resume/JD** are separate tables rather than a generic `context_documents` table for clearer product semantics and simpler queries.

---

## Next Steps (when implementing)

1. Create Alembic initial migration from this spec.
2. Add `set_updated_at()` trigger on mutable tables.
3. Implement repository layer with strict `user_id` scoping.
4. Build score extraction service: agent JSONB → `evaluation_scores` rows.
5. Add integration tests for session and answer evaluation run creation.

See [database-diagram.md](./database-diagram.md) for the ER diagram.
