from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from harness.schema import FAMILY_WEIGHTS, TaskFamily
from harness.tasks import load_task_map

CONSISTENCY = TaskFamily.CONSISTENCY_ADVERSARIAL.value


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _composite(family_means: dict[str, float]) -> float:
    return sum(FAMILY_WEIGHTS.get(fam, 0) * family_means.get(fam, 0) for fam in FAMILY_WEIGHTS)


def generate_report(run_dir: Path, tasks_dir: Path) -> dict:
    judgments = _load_jsonl(run_dir / "judged.jsonl")
    consistency = _load_jsonl(run_dir / "consistency.jsonl")
    task_map = load_task_map(tasks_dir)

    by_model: dict[str, list[dict]] = defaultdict(list)
    for j in judgments:
        by_model[j["model"]].append(j)

    # Family 6 is scored at the variant-group level, not per task.
    group_scores: dict[str, list[float]] = defaultdict(list)
    for c in consistency:
        group_scores[c["model"]].append(c["group_score"])

    report: dict = {"models": {}, "run_dir": str(run_dir)}

    for model, rows in by_model.items():
        family_scores: dict[str, list[float]] = defaultdict(list)
        prov_family_scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        failure_tags: Counter = Counter()

        for row in rows:
            task = task_map.get(row["task_id"])
            if not task:
                continue
            fam = task.family.value
            failure_tags.update(row.get("failure_tags") or [])
            if fam == CONSISTENCY:
                continue  # handled via group_scores
            family_scores[fam].append(row["final_score"])
            prov_family_scores[row.get("provenance", "canonical")][fam].append(row["final_score"])

        family_means = {fam: _mean(scores) for fam, scores in family_scores.items()}
        if group_scores.get(model):
            family_means[CONSISTENCY] = _mean(group_scores[model])

        # Composite per provenance stratum (family 6 shared across strata).
        provenance_composite = {}
        for prov, fams in prov_family_scores.items():
            means = {fam: _mean(s) for fam, s in fams.items()}
            if group_scores.get(model):
                means[CONSISTENCY] = _mean(group_scores[model])
            provenance_composite[prov] = round(_composite(means), 2)

        gap = None
        if "canonical" in provenance_composite and "novel" in provenance_composite:
            gap = round(provenance_composite["canonical"] - provenance_composite["novel"], 2)

        report["models"][model] = {
            "composite_score": round(_composite(family_means), 2),
            "family_scores": {k: round(v, 2) for k, v in family_means.items()},
            "task_count": len(rows),
            "top_failure_tags": failure_tags.most_common(5),
            "provenance_composite": provenance_composite,
            "canonical_minus_novel": gap,
            "consistency_groups": len(group_scores.get(model, [])),
        }

    out = run_dir / "report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def print_report(report: dict) -> None:
    from rich.console import Console
    from rich.table import Table

    console = Console()
    for model, data in report["models"].items():
        table = Table(title=f"AdvaitaBench — {model}")
        table.add_column("Family")
        table.add_column("Score", justify="right")
        for fam, score in sorted(data["family_scores"].items()):
            table.add_row(fam, f"{score:.1f}")
        table.add_row("[bold]Composite[/bold]", f"[bold]{data['composite_score']:.1f}[/bold]")
        console.print(table)

        if data.get("provenance_composite"):
            console.print("By provenance:", data["provenance_composite"],
                          f"(canonical − novel = {data.get('canonical_minus_novel')})")
        if data["top_failure_tags"]:
            console.print("Top failure tags:", data["top_failure_tags"])
        console.print()
