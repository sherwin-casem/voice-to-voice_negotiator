# Scoring Methodology

**Status:** MVP v1.0  
**Scope:** Transparent 0–100 scoring used by the Scoring Judge agent

The Scoring Judge combines **deterministic numeric rollup** (this document) with **LLM synthesis** for qualitative feedback. Numeric scores are authoritative; the judge LLM produces strengths, weaknesses, evidence, and priority improvements grounded in the candidate answer.

---

## Scale

| Layer | Range | Notes |
|-------|-------|-------|
| Specialist agent dimensions | 0–10 | Per rubric dimension in each specialist output |
| Normalized judge dimensions | 0–100 | `specialist_score × 10`, optionally blended |
| Overall score | 0–100 | Weighted sum of applicable normalized dimensions |

---

## Dimension mapping

Specialist outputs map to unified judge dimensions as follows:

| Judge dimension | Source |
|-----------------|--------|
| **communication** | Avg(communication.clarity, communication.tone) × 10 |
| **structure** | 65% communication.structure + 35% behavioral.star_method (when behavioral available) |
| **conciseness** | communication.conciseness × 10 |
| **confidence** | communication.confidence × 10 |
| **relevance** | Avg(relevance.role_alignment, jd_alignment, question_responsiveness, context_usage) × 10 |
| **technical** | Avg(technical.depth, technical.accuracy) × 10 — *technical/system_design interviews only* |
| **problem_solving** | Technical: avg(problem_solving, trade_off_awareness) × 10; Behavioral/HR/Leadership: avg(star_method, impact) × 10 |

When a specialist agent is **skipped**, **failed**, or **not applicable**, the judge uses:

- **Failed/missing communication, relevance, etc.:** neutral default of **50** for that dimension (signals uncertainty, not excellence)
- **Technical on behavioral/HR/leadership interviews:** `technical = null` (excluded from overall)
- **Problem solving on technical interviews without technical agent:** `null` (excluded)

---

## Interview-type weights

Overall score uses weighted dimensions. Weights are **renormalized** over applicable dimensions only (excluding `null` scores and zero-weight dimensions).

### Technical

| Dimension | Weight |
|-----------|--------|
| communication | 0.12 |
| technical | 0.28 |
| relevance | 0.15 |
| structure | 0.10 |
| confidence | 0.10 |
| conciseness | 0.05 |
| problem_solving | 0.20 |

### System design

Same as technical with higher problem_solving (0.27) and adjusted technical/relevance weights — see `INTERVIEW_WEIGHTS` in `scoring_model.py`.

### Behavioral / HR / Leadership

Technical weight is **0** (dimension excluded). Problem-solving weight reflects behavioral STAR/impact signals.

---

## Conflict resolution

The judge does **not** blindly average conflicting specialist scores.

### Communication vs relevance

When communication clarity exceeds question responsiveness by **≥ 25 points** (on 0–100 scale):

```
adjusted_communication = 0.4 × clarity + 0.6 × question_responsiveness
```

Rationale: fluent but off-topic answers should not receive full communication credit.

### Technical vs hiring manager

When |technical_readiness − hiring_manager.role_readiness| **> 25 points**:

- **Technical / system design interviews:** `0.7 × technical + 0.3 × hiring_manager`
- **Other types:** `0.35 × technical + 0.65 × hiring_manager`

Rationale: interview type determines which perspective dominates hire-readiness disagreements.

All resolutions are recorded in `conflict_resolutions` on the judge output.

---

## Overall score calculation

```
overall = Σ (dimension_score[d] × normalized_weight[d])   for applicable dimensions d
```

Where `normalized_weight[d] = base_weight[d] / Σ base_weight[applicable]`.

---

## Strongest / weakest dimensions

After normalization, dimensions are ranked by score:

- **Strongest:** top 2 applicable dimensions
- **Weakest:** bottom 2 applicable dimensions

These drive priority improvement recommendations.

---

## Judge output schema

`JudgeEvaluationOutput` includes:

| Field | Description |
|-------|-------------|
| `overall_score` | 0–100 weighted rollup |
| `dimension_scores` | Normalized dimension breakdown |
| `strengths` / `weaknesses` | Qualitative summary (LLM + mock) |
| `evidence` | Answer quotes tagged by dimension |
| `priority_improvements` | Actionable items tied to weak dimensions |
| `conflict_resolutions` | Human-readable conflict handling log |
| `weights_applied` | Renormalized weights used for overall score |
| `scoring_methodology_version` | `"1.0"` |

---

## Orchestration

```
Specialists (parallel) → ScoringModel.compute() → Judge LLM synthesis → JudgeEvaluationOutput
```

If LLM synthesis fails, the judge returns a **baseline fallback** using scoring model numbers and minimal evidence from the answer excerpt.

---

## Implementation

| Component | Path |
|-----------|------|
| Scoring model | `app/modules/evaluation/judge/scoring_model.py` |
| Judge agent | `app/modules/evaluation/agents/judge.py` |
| Output schema | `app/ai/schemas/evaluation/judge.py` |
| Prompts | `app/ai/prompts/evaluation/judge/v1/` |

---

## Related docs

- [evaluation-pipeline.md](./evaluation-pipeline.md)
- [architecture.md](./architecture.md) — §12–14
