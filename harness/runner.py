from __future__ import annotations

import json
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harness.providers import ModelFn, parse_spec, resolve_model_fn, uses_real_money
from harness.schema import ResponseRecord, Task, TaskFamily
from harness.tasks import build_messages, load_tasks

SYSTEM_PROMPTS = {
    "neutral": "Answer accurately about Advaita Vedānta.",
    "school_pinned": (
        "Answer from classical Advaita Vedānta (Śaṅkara tradition). "
        "Do not conflate Advaita with Dvaita, Viśiṣṭādvaita, Buddhism, Sāṃkhya, Yoga, "
        "or generic New Age non-duality unless explicitly asked to compare schools."
    ),
    "teacher": "Explain as an Advaita teacher would to a sincere student, with doctrinal precision.",
}

# AdvaitaBench is a closed-book benchmark: subject models get no tools, no
# retrieval, no web. Kept as a constant so the manifest records the condition
# and any future open-book track has to opt in explicitly.
CLOSED_BOOK = True


def new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{uuid.uuid4().hex[:8]}"


def _accumulate(usage_totals: dict[str, dict[str, float]], model: str, usage: dict[str, Any]) -> None:
    acc = usage_totals[model]
    acc["input_tokens"] += float(usage.get("input_tokens", 0) or 0)
    acc["output_tokens"] += float(usage.get("output_tokens", 0) or 0)
    acc["cost_usd"] += float(usage.get("cost_usd", 0) or 0)
    acc["calls"] += 1


def run_benchmark(
    tasks_dir: Path,
    models: list[str],
    output_dir: Path,
    system_condition: str = "school_pinned",
    family: str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
) -> Path:
    run_id = new_run_id()
    run_path = output_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(tasks_dir, family=family)
    if limit:
        tasks = tasks[:limit]
    system_prompt = SYSTEM_PROMPTS.get(system_condition, SYSTEM_PROMPTS["school_pinned"])

    provider_map = {m: parse_spec(m)[0] for m in models}
    paid = [m for m in models if uses_real_money(m)]

    manifest = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "models": models,
        "provider_map": provider_map,
        "openrouter_models": paid,
        "system_condition": system_condition,
        "closed_book": CLOSED_BOOK,
        "temperature": 0,
        "task_count": len(tasks),
        "tasks_dir": str(tasks_dir),
    }
    (run_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    usage_totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {"input_tokens": 0.0, "output_tokens": 0.0, "cost_usd": 0.0, "calls": 0}
    )
    errors: list[dict[str, str]] = []
    out = run_path / "responses.jsonl"

    def emit(f, rec: ResponseRecord) -> None:
        f.write(rec.model_dump_json() + "\n")

    def ask(model_fn: ModelFn, model: str, messages: list[dict[str, str]]) -> tuple[str, dict, int | None]:
        if dry_run or model_fn is None:
            return "[dry-run]", {}, None
        start = time.time()
        text, usage = model_fn(model, messages)
        latency = int((time.time() - start) * 1000)
        _accumulate(usage_totals, model, usage)
        return text, usage, latency

    with out.open("w", encoding="utf-8") as f:
        for model in models:
            try:
                model_fn = None if dry_run else resolve_model_fn(model)
            except Exception as exc:  # noqa: BLE001 - skip a whole model cleanly
                errors.append({"model": model, "task_id": "*", "error": str(exc)})
                print(f"  ! {model}: could not initialize ({exc}); skipping")
                continue

            for task in tasks:
                try:
                    _run_one_task(task, model, model_fn, system_prompt, run_id, ask, f, emit)
                except Exception as exc:  # noqa: BLE001 - one task failing must not sink the run
                    errors.append({"model": model, "task_id": task.id, "error": str(exc)})
                    print(f"  ! {model} / {task.id}: {exc}")

    # Fold usage + errors back into the manifest now that totals are known.
    manifest["usage_totals"] = {m: dict(v) for m, v in usage_totals.items()}
    manifest["openrouter_cost_usd"] = round(
        sum(v["cost_usd"] for m, v in usage_totals.items() if uses_real_money(m)), 4
    )
    manifest["errors"] = errors
    (run_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return run_path


def _run_one_task(task: Task, model, model_fn, system_prompt, run_id, ask, f, emit) -> None:
    messages = build_messages(task, system_prompt)

    is_multiturn = task.family == TaskFamily.MISCONCEPTION_REPAIR and task.follow_up_turns
    if not is_multiturn:
        text, usage, latency = ask(model_fn, model, messages)
        emit(f, ResponseRecord(
            run_id=run_id, task_id=task.id, model=model, system_prompt=system_prompt,
            messages=messages, response=text, latency_ms=latency, usage=usage,
        ))
        return

    # Multi-turn: seed the dialogue, then feed each scripted user pushback,
    # letting the conversation accumulate so the model answers in context.
    text, usage, latency = ask(model_fn, model, messages)
    emit(f, ResponseRecord(
        run_id=run_id, task_id=task.id, model=model, system_prompt=system_prompt,
        messages=messages, response=text, latency_ms=latency, usage=usage,
    ))

    convo = list(messages) + [{"role": "assistant", "content": text}]
    for turn in task.follow_up_turns:
        convo.append({"role": turn.role, "content": turn.content})
        if turn.role != "user":
            continue
        follow_up, usage, latency = ask(model_fn, model, convo)
        convo.append({"role": "assistant", "content": follow_up})
        user_turns = len([t for t in convo if t["role"] == "user"]) - 1
        emit(f, ResponseRecord(
            run_id=run_id, task_id=f"{task.id}@{user_turns}", model=model,
            system_prompt=system_prompt, messages=list(convo)[:-1], response=follow_up,
            latency_ms=latency, usage=usage,
        ))
