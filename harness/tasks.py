from __future__ import annotations

from pathlib import Path

import yaml

from harness.schema import Task, TaskFamily


def _str_list(value) -> list[str]:
    """Normalize a YAML list whose items may be strings or, thanks to an
    unquoted colon, single-key mappings (``- Term: gloss`` parses as a dict).
    Coerce those back to ``"Term: gloss"`` so scholarly notes need no quoting.
    """
    out: list[str] = []
    for item in value or []:
        if isinstance(item, dict):
            out.extend(f"{k}: {v}" for k, v in item.items())
        else:
            out.append(str(item))
    return out


def _parse_document(doc: dict) -> Task:
    family = TaskFamily(doc["family"])
    return Task(
        id=doc["id"],
        family=family,
        prompt=doc["prompt"].strip(),
        turns=doc.get("turns") or [],
        follow_up_turns=doc.get("follow_up_turns") or [],
        passage=doc.get("passage"),
        variant_group_id=doc.get("variant_group_id"),
        gold_doctrine_key=doc.get("gold_doctrine_key"),
        target_school=doc.get("target_school", "advaita"),
        contrast_school=doc.get("contrast_school"),
        language=doc.get("language", "en"),
        rubric_dimensions=doc["rubric_dimensions"],
        dimension_weights=doc.get("dimension_weights") or {},
        gold_points=_str_list(doc.get("gold_points")),
        required_distinctions=_str_list(doc.get("required_distinctions")),
        forbidden_claims=_str_list(doc.get("forbidden_claims")),
        reference_answer=(doc.get("reference_answer") or "").strip(),
        failure_tags_watch=doc.get("failure_tags_watch") or [],
        tags=doc.get("tags") or [],
        difficulty=doc.get("difficulty", "pilot"),
        provenance=doc.get("provenance", "canonical"),
    )


def load_tasks(tasks_dir: Path, family: str | None = None) -> list[Task]:
    tasks: list[Task] = []
    yaml_files = sorted(tasks_dir.glob("*.yaml"))

    for path in yaml_files:
        raw = path.read_text(encoding="utf-8")
        for doc in yaml.safe_load_all(raw):
            if not doc:
                continue
            task = _parse_document(doc)
            if family and task.family.value != family:
                continue
            tasks.append(task)

    return tasks


def load_task_map(tasks_dir: Path) -> dict[str, Task]:
    return {t.id: t for t in load_tasks(tasks_dir)}


def build_messages(task: Task, system_prompt: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    if task.passage:
        passage_block = (
            f"Passage ({task.passage.source}, tier {task.passage.tier}):\n\n{task.passage.text.strip()}"
        )
        messages.append({"role": "user", "content": passage_block})

    for turn in task.turns:
        messages.append({"role": turn.role, "content": turn.content})

    messages.append({"role": "user", "content": task.prompt.strip()})
    return messages


def build_multiturn_messages(
    task: Task, system_prompt: str, assistant_opener: str | None = None
) -> list[list[dict[str, str]]]:
    """Return message lists for each turn of a misconception-repair dialogue."""
    base = build_messages(task, system_prompt)
    stages: list[list[dict[str, str]]] = [base]

    if not task.follow_up_turns:
        return stages

    convo = list(base)
    if assistant_opener:
        convo.append({"role": "assistant", "content": assistant_opener})

    for turn in task.follow_up_turns:
        convo.append({"role": turn.role, "content": turn.content})
        if turn.role == "user":
            stages.append(list(convo))

    return stages
