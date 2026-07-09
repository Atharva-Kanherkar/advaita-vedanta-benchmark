"""Two-judge normalized scoring (AdvaitaBench-N).

Both judges exhibit measurable same-family preference (Haiku 4.5 ranked Claude
models 1-2; GPT-5.4 penalized GPT subjects ~5 pts less than others and ranked
them 1-2; Kendall tau between the rankings is only ~0.3). A manual audit also
found one systematic strict-judge cap misfire. This script produces the
corrected, normalized leaderboard:

1. Cap-misfire fix: `text_ungrounded` (cap 20) only applies when the judge's own
   `textual_evidence` score is <= 1 — i.e. the passage genuinely was not cited.
   Citing *additional* canonical material is not "ungrounded".
2. Per-judge standardization: composite c_ij -> z_ij = (c_ij - mu_j) / sigma_j.
3. Self-preference correction (difference-in-differences): for judge j with
   model family F_j, sp_j = mean_{i in F_j}(z_ij - z_i,other), applied only if
   positive; corrected z'_ij = z_ij - sp_j for i in F_j.
4. AdvaitaBench-N = 50 + 15 * mean_j(z'_ij)  (T-score scale).

Writes results/normalized.json.
"""
from __future__ import annotations

import json
import statistics as st
from collections import defaultdict
from pathlib import Path

from harness.schema import FAMILY_WEIGHTS, TaskFamily, apply_caps
from harness.tasks import load_task_map

RUN = Path("runs/20260708T170203Z-2dfb2836")
OUT = Path("results")
OUT.mkdir(exist_ok=True)

JUDGES = {
    "strict": ("judged.jsonl", "openai"),          # GPT-5.4, strict rubric v2
    "lenient": ("judged_haiku_lenient.jsonl", "anthropic"),  # Haiku 4.5, rubric v1
}
FAMILY_OF = {"openai": lambda m: m.startswith("openai:") or "gpt" in m,
             "anthropic": lambda m: m.startswith("anthropic:")}

task_map = load_task_map(Path("tasks"))


def capfixed_final(j: dict) -> float:
    """Recompute final score with the text_ungrounded misfire fix."""
    task = task_map.get(j["task_id"])
    if not task:
        return j["final_score"]
    tags = list(j.get("failure_tags") or [])
    dims = j.get("dimension_scores") or {}
    if "text_ungrounded" in tags and dims.get("textual_evidence", 0) >= 2:
        tags.remove("text_ungrounded")  # passage was cited; tag misapplied
    final, _, _ = apply_caps(task, j["raw_score"], tags, dims)
    return final


def composites(path: Path) -> dict[str, float]:
    fam_scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        j = json.loads(line)
        task = task_map.get(j["task_id"])
        if not task:
            continue
        fam_scores[j["model"]][task.family.value].append(capfixed_final(j))
    comp = {}
    for m, fams in fam_scores.items():
        means = {f: st.mean(v) for f, v in fams.items()}
        comp[m] = sum(FAMILY_WEIGHTS.get(f, 0) * means.get(f, 0) for f in FAMILY_WEIGHTS)
    return comp


def family_scores_strict() -> dict[str, dict[str, float]]:
    fam: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for line in (RUN / JUDGES["strict"][0]).read_text().splitlines():
        if not line.strip():
            continue
        j = json.loads(line)
        task = task_map.get(j["task_id"])
        if task:
            fam[j["model"]][task.family.value].append(capfixed_final(j))
    return {m: {f: round(st.mean(v), 1) for f, v in fams.items()} for m, fams in fam.items()}


comp = {name: composites(RUN / fn) for name, (fn, _) in JUDGES.items()}
models = sorted(set(comp["strict"]) & set(comp["lenient"]))

z = {}
for name in JUDGES:
    vals = [comp[name][m] for m in models]
    mu, sd = st.mean(vals), st.pstdev(vals)
    z[name] = {m: (comp[name][m] - mu) / sd for m in models}

# Difference-in-differences self-preference per judge.
sp = {}
for name, (_, fam_key) in JUDGES.items():
    other = next(n for n in JUDGES if n != name)
    own = [m for m in models if FAMILY_OF[fam_key](m)]
    sp[name] = max(0.0, st.mean(z[name][m] - z[other][m] for m in own)) if own else 0.0

zc = {name: {m: z[name][m] - (sp[name] if FAMILY_OF[fam_key](m) else 0.0)
             for m in models}
      for name, (_, fam_key) in JUDGES.items()}

normalized = {m: 50 + 15 * st.mean(zc[n][m] for n in JUDGES) for m in models}
fam_strict = family_scores_strict()

result = {
    "formula": "AdvaitaBench-N = 50 + 15 * mean_j( z_ij - sp_j*1[i in family(j)] ); "
               "z per-judge standardized composite; sp_j = DiD self-preference; "
               "text_ungrounded cap only when textual_evidence<=1",
    "self_preference": {n: round(v, 3) for n, v in sp.items()},
    "models": {
        m: {
            "normalized": round(normalized[m], 1),
            "strict_composite": round(comp["strict"][m], 1),
            "lenient_composite": round(comp["lenient"][m], 1),
            "family_scores_strict": fam_strict.get(m, {}),
        }
        for m in models
    },
}
(OUT / "normalized.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

print(f"self-preference corrections: {result['self_preference']}")
print(f"{'model':<30}{'AdvaitaBench-N':>15}{'strict':>9}{'lenient':>9}")
for m in sorted(models, key=lambda m: -normalized[m]):
    d = result["models"][m]
    print(f"{m.split(':')[-1].split('/')[-1]:<30}{d['normalized']:>15.1f}{d['strict_composite']:>9.1f}{d['lenient_composite']:>9.1f}")
print("\nwrote results/normalized.json")
