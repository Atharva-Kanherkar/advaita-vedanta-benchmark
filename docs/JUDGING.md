# AdvaitaBench Judging Specification

This document defines how responses become scores. The harness implements this via `harness/judge.py` and prompt templates in `judges/`.

---

## 1. Judge roles

| Role | Input | Output |
|------|-------|--------|
| **Rubric judge** | Task spec + model response(s) | Dimension scores, tags, rationale |
| **Consistency judge** | Variant group responses + doctrine signatures | Consistency distance, drift flags |
| **Human adjudicator** | Same bundle, blinded | Final score on disputed items |

---

## 2. Rubric judge protocol

### 2.1 Independence requirements

- Judge model **≠** subject model — **enforced** by the harness (`judge_run` raises `SelfJudgeError` if the judge id matches any subject id; `--allow-self-judge` overrides and flags the run non-publication-grade)
- Temperature **0**
- Judge receives: task prompt, rubric dimensions, `reference_answer`, `gold_points`, `forbidden_claims`, `required_distinctions`, response(s), and — for multi-turn tasks — the **full conversation transcript** (all user + assistant turns)
- Judge does **not** receive: model name, prior run history, other models’ answers (unless consistency group)
- Judge is instructed to grade **against the reference material**, not from its own parametric knowledge

### 2.2 Judge output schema

The judge emits **only** the fields below — no score, no cap. The harness owns
scoring so a judge cannot anchor its dimension marks to a target number.

```json
{
  "task_id": "cp-001",
  "dimension_scores": {
    "term_accuracy": 3,
    "distinction_clarity": 4
  },
  "failure_tags": [],
  "rationale": "Correctly distinguishes jīva and Ātman via upādhi; minor imprecision on avidyā.",
  "doctrine_signature": {
    "core_claim": "jiva is atman plus limiting adjuncts under avidya",
    "levels_used": ["vyavaharika", "paramarthika"],
    "school": "advaita",
    "key_distinctions": ["jiva vs atman"]
  }
}
```

### 2.3 Scoring algorithm

1. Judge assigns 0–4 per dimension (dimension names not in the task rubric are ignored; omitted dimensions are logged)
2. Harness computes weighted mean → raw 0–100 (weights from the task or uniform)
3. Apply **automatic caps** from `RUBRICS.md` if failure tags trigger (`school_mixing`/`new_age_nonduality` cap in every family; `level_collapse`/`nihilistic_denial` in level-of-reality and misconception-repair; `text_ungrounded` in text-grounded; tightest cap wins)
4. Store both `raw_score` and `final_score`

```python
raw = 100 * sum(w[d] * s[d] for d in dimensions) / 4
final = min(raw, cap) if cap else raw
```

### 2.4 Forbidden claims check

If response asserts any string in `forbidden_claims` (substring or semantic match via judge), auto-apply:
- Tag relevant failure mode
- Cap per rubric rules

Judge prompt includes: “Treat these as **automatic failures** if affirmed: …”

---

## 3. Consistency judge protocol

For tasks sharing `variant_group_id`:

1. Rubric judge scores each variant independently
2. Consistency judge extracts `doctrine_signature` per variant
3. Compare signatures on:
   - `core_claim` (semantic equivalence)
   - `levels_used` (set equality or justified subset)
   - `school` (must match)
   - `key_distinctions` (must not contradict)

**Distance levels:**

| Distance | Meaning |
|----------|---------|
| 0 | Doctrinally equivalent |
| 1 | Same doctrine, different emphasis |
| 2 | Partial contradiction |
| 3 | Direct contradiction |

Group fails robustness if any pair has distance ≥ 2.

---

## 4. Multi-turn judging

For `misconception_repair` and multi-turn tasks:

- Judge sees the **full transcript** (all user + assistant turns). The harness
  reconstructs it from the final response record's `messages` (which already
  accumulate the whole dialogue) plus its final answer — passed as the judge's
  prior-conversation context, with the last assistant turn as the graded response.
- Turn-level flags recorded but **conversation-level dimensions** determine score
- Early correct + late capitulation → `dialogue_stability ≤ 1`, tag `sycophantic_agreement`

---

## 5. Human adjudication

### 5.1 Sample selection

- Random 10% of tasks per run (min 5)
- Oversample: any task where two automated judge runs disagree by >15 points
- Oversample: all `text_grounded` Tier A tasks until κ stable

### 5.2 Annotator requirements

- Familiarity with Advaita terminology (self-declared + calibration set)
- Complete calibration: 5 tasks with known scores, must reach ≥80% within 1 point

### 5.3 Agreement metrics

Report:
- Cohen’s κ (quadratic weighted for 0–4)
- Mean absolute deviation (judge vs human)
- Disagreement taxonomy (which dimensions drift)

Publication threshold: **κ ≥ 0.65** on adjudicated subset.

---

## 6. Judge prompts

Templates live in `judges/rubric_judge.txt` and `judges/consistency_judge.txt`.

Design rules:
- Lead with role: “You are an Advaita Vedānta examiner, not a spiritual counselor.”
- Require JSON only in final message
- Include negative examples (what **not** to reward)
- Explicit: “Do not penalize Sanskrit/IAST if concepts are correct”

---

## 7. Sensitivity analysis (publication)

Run and report:

| Variable | Values |
|----------|--------|
| Judge model | ≥2 models |
| Judge prompt version | v1 vs v1.1 |
| System prompt condition | neutral vs school_pinned |

Report rank stability (Kendall τ) across judge models.

---

## 8. Reproducibility artifacts

Each judged run writes:

```
runs/<run_id>/
  config.yaml          # frozen
  responses.jsonl      # subject outputs
  judged.jsonl           # scores + rationales
  manifest.json          # task hashes, model IDs, judge ID, timestamps
  failures/              # per-tag exemplars for qualitative appendix
```

Task content hashed with SHA-256 of canonical JSON (sorted keys).
