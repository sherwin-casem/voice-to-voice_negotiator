# Context Preparation Layer

**Status:** MVP  
**Module:** `app/modules/context/`

This document describes how resume and job-description content is parsed once, stored as structured JSON, and served to interview and evaluation agents through compact, step-specific context slices.

---

## Goals

1. Accept resume and job description input (paste or plain-text upload).
2. Extract structured fields: skills, experience, projects, responsibilities, likely interview topics, and evaluation rubric hints.
3. Personalize interviewer questions, difficulty calibration, follow-ups, and evaluation rubric focus.
4. Avoid sending full raw documents to every LLM call.

---

## Architecture

```
Upload / paste
      │
      ▼
ContextPreparationService.prepare_resume / prepare_job_description
      │
      ├── HeuristicContextExtractor (AI_PROVIDER=mock)
      └── LLMContextExtractor (AI_PROVIDER=openai)
      │
      ▼
Persist parsed JSON + summary_text + parse_status
      │
      ▼
ContextSelector.select(bundle, InterviewStep.*)
      │
      ├── InterviewerAgent prompts
      └── EvaluationContext builder
```

| Component | Responsibility |
|-----------|----------------|
| `ContextRepository` | Read/write resumes and job descriptions |
| `HeuristicContextExtractor` | Deterministic parsing for tests/dev |
| `LLMContextExtractor` | Structured extraction via versioned prompts |
| `ContextSelector` | Step-specific compact slices |
| `ContextPreparationService` | Orchestration and interview/evaluation builders |

---

## Structured schemas

### Resume (`parsed_profile`)

- `skills`, `experience[]`, `projects[]`, `responsibilities[]`
- `likely_interview_topics`, `years_experience`, `headline`, `summary_text`

### Job description (`parsed_requirements`)

- `required_skills`, `preferred_skills`, `responsibilities[]`
- `technical_topics[]`, `behavioral_topics[]`, `likely_interview_topics[]`
- `evaluation_rubric_hints[]`, `experience_level`, `summary_text`

Schemas live in `app/ai/schemas/context/`.

---

## Interview steps

| Step | Used by | Selected fields |
|------|---------|-----------------|
| `interviewer_opening` | First question | summaries, top skills, JD requirements, uncovered topics |
| `interviewer_follow_up` | Follow-up questions | topic-matched skills/projects, remaining topics |
| `evaluation_answer` | Per-answer evaluation | role alignment skills/responsibilities + rubric hints |
| `evaluation_rubric` | Specialist/judge prompts | type-weighted technical/behavioral focus + rubric hints |
| `coach` | Improvement coach | compact profile + rubric hints |

Selection limits (defaults):

- Summary text: 600 characters
- List items: 8 entries × 120 characters

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/context/resumes` | Paste resume text, run preparation |
| `POST` | `/api/v1/context/resumes/upload` | Upload plain-text resume file |
| `GET` | `/api/v1/context/resumes/{id}` | Fetch prepared resume summary |
| `POST` | `/api/v1/context/job-descriptions` | Paste JD text, run preparation |
| `POST` | `/api/v1/context/job-descriptions/upload` | Upload plain-text JD file |
| `GET` | `/api/v1/context/job-descriptions/{id}` | Fetch prepared JD summary |

On session configure (`PATCH /sessions/{id}`), linked documents are prepared automatically if still `pending`.

---

## Personalization behavior

### Interviewer

- Opening questions prioritize uncovered `likely_interview_topics`.
- Follow-ups match the current topic tag against skills/projects.
- Difficulty uses JD `experience_level`, configured difficulty, or inferred resume seniority.
- Prompt version **1.1** injects selected structured fields instead of raw documents.

### Evaluation

- `EvaluationContext` includes selected skills, responsibilities, focus areas, and rubric hints.
- Relevance and hiring-manager prompts consume prepared summaries and rubric hints.
- Raw documents are never passed once structured preparation succeeds.

---

## Mock vs OpenAI

| Mode | Extractor |
|------|-----------|
| `AI_PROVIDER=mock` | `HeuristicContextExtractor` |
| `AI_PROVIDER=openai` | `LLMContextExtractor` + prompts in `app/ai/prompts/context/extractor/v1/` |

---

## Future work

- PDF/DOCX parsing pipeline
- Background re-preparation jobs
- Retrieval over chunked resume/JD sections
- Session-level context cache invalidation when documents change

---

## Related docs

- [database.md](./database.md) — `parsed_profile` / `parsed_requirements` columns
- [interview-domain.md](./interview-domain.md) — session lifecycle
- [scoring-methodology.md](./scoring-methodology.md) — evaluation rubric usage
