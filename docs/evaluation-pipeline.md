# Evaluation Pipeline

**Status:** MVP (specialist agents + scoring judge + improvement coach)  
**Scope:** Multi-agent evaluation with judge rollup and actionable coaching; REST persistence not yet implemented

This document describes the evaluation framework for the Voice-to-Voice Interview Negotiator backend.

---

## Overview

After a candidate submits an answer (or when a full session completes), the system can run **specialist evaluation agents** that independently score different dimensions of performance.

Each agent:

- Receives the same structured `EvaluationContext`
- Uses a **versioned prompt** with an explicit rubric
- Returns a **Pydantic-validated structured output**
- Does **not** write to the database directly
- Reports **execution metadata** (model, latency, success/failure)

A central **`EvaluationService`** orchestrates specialist agents in **parallel**, then runs the **Scoring Judge** and **Improvement Coach** sequentially. Individual agent failures are isolated and do not fail the entire run.

**Not implemented yet:** REST persistence layer, background job queue.

---

## Architecture

```
EvaluationContext
        │
        ▼
EvaluationService (orchestrator)
        │
        ├── CommunicationEvaluator ──┐
        ├── TechnicalEvaluator     │
        ├── BehavioralEvaluator    ├── asyncio.gather (parallel)
        ├── RelevanceEvaluator     │
        └── HiringManagerEvaluator ┘
                │
                ▼
        Scoring Judge (sequential)
                │
                ▼
        Improvement Coach (sequential)
                │
                ▼
        JudgeEvaluationOutput + ImprovementCoachOutput
                │
                ▼
   (future) repository persists evaluation_runs + agent_evaluations
```

### Layer responsibilities

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Schemas | `app/ai/schemas/evaluation/` | Structured agent output models |
| Prompts | `app/ai/prompts/evaluation/*/v1/` | Versioned rubrics and message builders |
| Evaluators | `app/modules/evaluation/agents/` | Agent logic via `BaseEvaluator` |
| Gating | `app/modules/evaluation/gating.py` | Interview-type skip rules |
| Orchestrator | `app/modules/evaluation/service.py` | Parallel specialists + sequential judge |
| Scoring model | `app/modules/evaluation/judge/scoring_model.py` | Transparent 0–100 rollup |
| Judge agent | `app/modules/evaluation/agents/judge.py` | Final structured evaluation |
| Improvement coach | `app/modules/evaluation/agents/coach.py` | Actionable coaching feedback |
| Factory | `app/modules/evaluation/factory.py` | Wire mock or OpenAI structured provider |

---

## Evaluation context

All specialist agents receive `EvaluationContext`:

| Field | Description |
|-------|-------------|
| `interview_type` | `behavioral`, `technical`, `system_design`, `leadership`, `hr` |
| `difficulty` | `junior`, `mid`, `senior` |
| `question_text` | Question being evaluated |
| `answer_text` | Candidate answer transcript |
| `scope` | `answer` or `session` |
| `target_role` | Optional role title |
| `company_context` | Optional company notes |
| `resume_summary` | Optional resume summary |
| `job_description_summary` | Optional JD summary |
| `topic_tag` | Optional question topic |
| `prior_turns` | Prior Q&A for conversational context |
| `session_id` / `answer_id` | Optional identifiers for future persistence |

---

## Specialist agents

### 1. Communication Evaluator

**Agent name:** `communication_evaluation`  
**Prompt:** `app/ai/prompts/evaluation/communication/v1/`  
**Output:** `CommunicationEvaluationOutput`

| Dimension | Rubric focus |
|-----------|--------------|
| clarity | Easy to follow, precise language |
| structure | Organized flow |
| conciseness | Complete without rambling |
| confidence | Assured but professional |
| tone | Interview-appropriate tone |

### 2. Technical Evaluator

**Agent name:** `technical_evaluation`  
**Skipped for:** `behavioral`, `leadership`, `hr`

| Dimension | Rubric focus |
|-----------|--------------|
| depth | Technical depth for difficulty level |
| accuracy | Correct, qualified claims |
| problem_solving | Sound approach |
| trade_off_awareness | Alternatives and constraints |

### 3. Behavioral Evaluator

**Agent name:** `behavioral_evaluation`  
**Skipped for:** `technical`, `system_design`

| Dimension | Rubric focus |
|-----------|--------------|
| star_method | STAR-style storytelling |
| ownership | Personal accountability |
| collaboration | Teamwork signals |
| impact | Articulated outcomes |

### 4. Relevance Evaluator

**Agent name:** `relevance_evaluation`  
**Always runs**

| Dimension | Rubric focus |
|-----------|--------------|
| role_alignment | Fit for target role |
| jd_alignment | Connection to job requirements |
| question_responsiveness | Directly answers the question |
| context_usage | Appropriate use of resume/JD context |

### 5. Hiring Manager Evaluator

**Agent name:** `hiring_manager_evaluation`  
**Always runs**

| Dimension | Rubric focus |
|-----------|--------------|
| role_readiness | Near-term performance potential |
| culture_fit | Alignment with company context |
| growth_potential | Learning trajectory |
| risk_assessment | Remaining hiring risks |

Also returns `hire_recommendation` (`strong_hire` … `no_hire`) and `decision_rationale`.

---

## Orchestration flow

```python
from app.modules.evaluation import EvaluationContext, build_evaluation_service
from app.db.enums import InterviewType

service = build_evaluation_service()
context = EvaluationContext(
    interview_type=InterviewType.TECHNICAL,
    difficulty="mid",
    question_text="...",
    answer_text="...",
)
result = await service.evaluate(context)
```

### Parallel execution

All registered specialists are invoked concurrently via `asyncio.gather`.

### Failure isolation

If an individual agent raises an exception, `BaseEvaluator` catches it and returns:

```python
AgentExecutionResult(status=FAILED, error_message="...", ...)
```

Other agents continue unaffected. The run is `COMPLETED` if at least one agent succeeds.

### Skip handling

Gated agents return `SKIPPED` with `skip_reason` instead of calling the LLM.

---

## Execution metadata

Each `AgentExecutionResult` includes:

| Field | Description |
|-------|-------------|
| `agent_name` | Enum identifier |
| `status` | `completed`, `failed`, or `skipped` |
| `schema_version` | Output schema version (e.g. `1.0`) |
| `prompt_version` | Prompt template version (e.g. `1.0`) |
| `model_id` | Model used (`mock-structured` or OpenAI model name) |
| `latency_ms` | Wall-clock execution time |
| `started_at` / `completed_at` | UTC timestamps |
| `error_message` | Present on failure |
| `output` | Structured Pydantic model on success |

Use `to_metadata_dict()` for logging or future DB persistence into `agent_evaluations`.

---

## Provider wiring

Controlled by `AI_PROVIDER`:

| Mode | LLM backend |
|------|-------------|
| `mock` | `MockEvaluationLLMProvider` — deterministic structured outputs for tests |
| `openai` | `StructuredOutputProvider` via `build_ai_providers()` |

Evaluators never import the OpenAI SDK directly.

---

## Database alignment (future)

Existing tables (see `docs/database.md`):

- `evaluation_runs` — run-level status and orchestration version
- `agent_evaluations` — per-agent JSON output + metadata
- `evaluation_scores` — normalized dimension scores
- `evaluation_results` — judge rollup (**future**)

The evaluation service currently returns in-memory results only. A repository layer will map `AgentExecutionResult` → `agent_evaluations` rows without changing agent code.

---

## Testing

```bash
cd apps/api
uv run pytest tests/evaluation -q
```

Tests use `MockEvaluationLLMProvider` and cover:

- Gating rules per interview type
- Structured outputs for all five agents
- Parallel orchestration
- Single-agent failure tolerance
- Prompt context assembly

See [scoring-methodology.md](./scoring-methodology.md) for the full 0–100 scoring model.

---

## Scoring Judge

After specialists complete, the **Scoring Judge** (`scoring_judge`):

1. Computes normalized 0–100 dimension scores via `ScoringModel` (deterministic, transparent)
2. Resolves conflicts between specialists (e.g., high clarity but low responsiveness)
3. Calculates weighted overall score by interview type
4. Synthesizes strengths, weaknesses, evidence, and priority improvements (LLM or mock)
5. Returns `JudgeEvaluationOutput` without writing to the database

---

## Improvement Coach

After the judge completes, the **Improvement Coach** (`improvement_coach`):

1. Receives the candidate answer, question, specialist outputs, judge scores, profile, and historical weaknesses
2. Produces **specific, evidence-based** coaching (schema rejects generic phrases)
3. Returns `ImprovementCoachOutput` with did-well, should-improve, highest priority, example answer, and practice exercise

See output fields in `app/ai/schemas/evaluation/coach.py`.

---

## Related docs

- [architecture.md](./architecture.md) — §12–14 multi-agent evaluation design
- [scoring-methodology.md](./scoring-methodology.md) — 0–100 scoring model
- [ai-integration.md](./ai-integration.md) — provider layer
- [interview-domain.md](./interview-domain.md) — interview lifecycle
- [database.md](./database.md) — evaluation tables
