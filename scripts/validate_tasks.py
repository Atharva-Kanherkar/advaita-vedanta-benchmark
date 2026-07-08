from __future__ import annotations

from pathlib import Path

import yaml

from harness.schema import PROVENANCE_VALUES, TaskFamily
from harness.tasks import load_tasks


REQUIRED_FIELDS = {"id", "family", "prompt", "rubric_dimensions"}


def validate(tasks_dir: Path) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    try:
        tasks = load_tasks(tasks_dir)
    except Exception as exc:
        return [f"Failed to load tasks: {exc}"]

    variant_groups: dict[str, list[str]] = {}

    for task in tasks:
        if task.id in seen_ids:
            errors.append(f"Duplicate task id: {task.id}")
        seen_ids.add(task.id)

        for dim in task.rubric_dimensions:
            if not dim:
                errors.append(f"{task.id}: empty rubric dimension")

        if task.family == TaskFamily.TEXT_GROUNDED and not task.passage:
            errors.append(f"{task.id}: text_grounded requires passage")

        if task.family == TaskFamily.CONSISTENCY_ADVERSARIAL:
            if not task.variant_group_id:
                errors.append(f"{task.id}: consistency task needs variant_group_id")
            else:
                variant_groups.setdefault(task.variant_group_id, []).append(task.id)

        if task.family == TaskFamily.MISCONCEPTION_REPAIR and not task.gold_points:
            errors.append(f"{task.id}: misconception_repair should have gold_points")

        if task.provenance not in PROVENANCE_VALUES:
            errors.append(
                f"{task.id}: provenance '{task.provenance}' not in {PROVENANCE_VALUES}"
            )

        weights = task.dimension_weights
        if weights:
            total = sum(weights.get(d, 0) for d in task.rubric_dimensions)
            if abs(total - 1.0) > 0.01:
                errors.append(f"{task.id}: dimension_weights sum to {total:.2f}, expected 1.0")

    for group, ids in variant_groups.items():
        if len(ids) < 2:
            errors.append(f"Variant group {group} has only {len(ids)} task(s)")

    return errors


if __name__ == "__main__":
    import sys

    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tasks")
    errs = validate(path)
    if errs:
        print("\n".join(errs))
        sys.exit(1)
    print("OK")
