# Progress Analysis

**Status:** MVP  
**Module:** `app/modules/progress/`  
**API:** `GET /api/v1/progress`

This document describes longitudinal interview performance tracking across multiple completed sessions.

---

## Tracked dimensions

All scores use the judge rollup scale (0–100):

| Dimension | Key |
|-----------|-----|
| Overall | `overall` |
| Communication | `communication` |
| Technical knowledge | `technical` |
| Relevance | `relevance` |
| Structure | `structure` |
| Conciseness | `conciseness` |
| Confidence | `confidence` |
| Problem solving | `problem_solving` |

Technical and problem-solving trends are computed only on `technical` and `system_design` interview sessions.

---

## Architecture

```
Session evaluation complete
        │
        ▼
ProgressAnalysisService.build_record_from_evaluation()
        │
        ├── Judge dimension scores
        ├── Answer metrics (word count, text)
        └── Pattern signal extraction
        │
        ▼
user_progress_snapshots (JSONB dimension_scores + _progress_meta)
        │
        ▼
ProgressAnalysisService.analyze_user()
        │
        ├── Difficulty-aware normalization
        ├── Dimension trends (recent vs prior window)
        ├── Recurring weakness detection
        └── Narrative summary
```

| Component | Role |
|-----------|------|
| `signals.py` | Detect per-session weakness patterns from answers + specialist scores |
| `patterns.py` | Aggregate recurring patterns across sessions |
| `normalizer.py` | Compare scores across difficulty and interview type |
| `service.py` | Orchestrate analysis and narrative generation |
| `repository.py` | Persist/read `user_progress_snapshots` |

---

## Weakness patterns

| Pattern | Detection signal |
|---------|------------------|
| `long_answers` | Word count ≥ 220 |
| `filler_words` | ≥ 3 filler tokens (um, like, you know, …) |
| `weak_star_structure` | Behavioral `star_method` score < 6 |
| `weak_trade_off_discussion` | Technical `trade_off_awareness` score < 6 |
| `poor_answer_opening` | Weak opening phrase or delayed main point |
| `weak_conclusion` | Trailing uncertainty / no clear takeaway |
| `lack_of_concrete_examples` | No measurable or concrete detail in answer text |

A pattern is **persistent** when it appears in at least 2 sessions and ≥ 40% of the analyzed window.

---

## Normalization (not raw score comparison)

Trend analysis compares **difficulty-adjusted** scores:

| Difficulty | Offset applied |
|------------|----------------|
| junior | +4 |
| mid | 0 |
| senior | -4 |

Technical dimensions are excluded from behavioral/HR session cohorts.

Trend direction thresholds:

- **Improving:** recent window average ≥ prior window + 3
- **Declining:** recent window average ≤ prior window − 3
- **Stable:** otherwise

---

## Narrative output

Example:

> You have improved in technical knowledge across your last 5 interviews, but overly long answers remains your most persistent weakness.

Narratives combine:

- Improving dimensions (normalized trends)
- Most persistent recurring weakness patterns
- Optional conciseness note when not improving

---

## API

```
GET /api/v1/progress?window=5
X-User-Id: {uuid}
```

Returns dimension trends, recurring weaknesses, improvements, persistent weaknesses, and `narrative_summary`.

---

## Coach integration

`ProgressAnalysisService.get_historical_weaknesses(user_id)` returns persistent pattern labels for the improvement coach prompt context.

---

## Related docs

- [scoring-methodology.md](./scoring-methodology.md)
- [database.md](./database.md) — `user_progress_snapshots`
- [evaluation-pipeline.md](./evaluation-pipeline.md)
