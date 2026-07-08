from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from harness.schema import FAMILY_WEIGHTS
from harness.tasks import load_task_map


def load_judgments(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def generate_report(run_dir: Path, tasks_dir: Path) -> dict:
    judged_path = run_dir / "judged.jsonl"
    judgments = load_judgments(judged_path)
    task_map = load_task_map(tasks_dir)

    by_model: dict[str, list[dict]] = defaultdict(list)
    for j in judgments:
        by_model[j["model"]].append(j)

    report: dict = {"models": {}, "run_dir": str(run_dir)}

    for model, rows in by_model.items():
        family_scores: dict[str, list[float]] = defaultdict(list)
        failure_tags: Counter = Counter()

        for row in rows:
            task = task_map.get(row["task_id"])
            if not task:
                continue
            family_scores[task.family.value].append(row["final_score"])
            failure_tags.update(row.get("failure_tags") or [])

        family_means = {
            fam: sum(scores) / len(scores) if scores else 0.0
            for fam, scores in family_scores.items()
        }

        composite = sum(
            FAMILY_WEIGHTS.get(fam, 0) * family_means.get(fam, 0)
            for fam in FAMILY_WEIGHTS
        )

        report["models"][model] = {
            "composite_score": round(composite, 2),
            "family_scores": {k: round(v, 2) for k, v in family_means.items()},
            "task_count": len(rows),
            "top_failure_tags": failure_tags.most_common(5),
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

        if data["top_failure_tags"]:
            console.print("Top failure tags:", data["top_failure_tags"])
