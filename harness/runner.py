from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from harness.schema import ResponseRecord
from harness.tasks import build_messages, build_multiturn_messages, load_tasks
from harness.schema import Task, TaskFamily


SYSTEM_PROMPTS = {
    "neutral": "Answer accurately about Advaita Vedānta.",
    "school_pinned": (
        "Answer from classical Advaita Vedānta (Śaṅkara tradition). "
        "Do not conflate Advaita with Dvaita, Viśiṣṭādvaita, Buddhism, Sāṃkhya, Yoga, "
        "or generic New Age non-duality unless explicitly asked to compare schools."
    ),
    "teacher": "Explain as an Advaita teacher would to a sincere student, with doctrinal precision.",
}


ModelFn = Callable[[str, list[dict[str, str]]], tuple[str, dict[str, Any]]]


def _openai_model(model: str) -> ModelFn:
    from openai import OpenAI

    client = OpenAI()

    def call(_model: str, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
        resp = client.chat.completions.create(model=model, messages=messages, temperature=0)
        text = resp.choices[0].message.content or ""
        usage = {
            "input_tokens": resp.usage.prompt_tokens if resp.usage else 0,
            "output_tokens": resp.usage.completion_tokens if resp.usage else 0,
        }
        return text, usage

    return call


def _anthropic_model(model: str) -> ModelFn:
    from anthropic import Anthropic

    client = Anthropic()

    def call(_model: str, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
        system = ""
        chat: list[dict[str, str]] = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                chat.append(m)
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=chat,
            temperature=0,
        )
        text = resp.content[0].text if resp.content else ""
        usage = {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        }
        return text, usage

    return call


def resolve_model_fn(model: str) -> ModelFn:
    if model.startswith("claude"):
        return _anthropic_model(model)
    return _openai_model(model)


def new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{uuid.uuid4().hex[:8]}"


def run_benchmark(
    tasks_dir: Path,
    models: list[str],
    output_dir: Path,
    system_condition: str = "school_pinned",
    family: str | None = None,
    dry_run: bool = False,
) -> Path:
    run_id = new_run_id()
    run_path = output_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(tasks_dir, family=family)
    system_prompt = SYSTEM_PROMPTS.get(system_condition, SYSTEM_PROMPTS["school_pinned"])
    records: list[ResponseRecord] = []

    manifest = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "models": models,
        "system_condition": system_condition,
        "task_count": len(tasks),
        "tasks_dir": str(tasks_dir),
    }
    (run_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    for model in models:
        model_fn = None if dry_run else resolve_model_fn(model)
        for task in tasks:
            if task.family == TaskFamily.MISCONCEPTION_REPAIR and task.follow_up_turns:
                messages = build_messages(task, system_prompt)
                if dry_run:
                    records.append(
                        ResponseRecord(
                            run_id=run_id,
                            task_id=task.id,
                            model=model,
                            system_prompt=system_prompt,
                            messages=messages,
                            response="[dry-run]",
                        )
                    )
                    continue

                start = time.time()
                response, usage = model_fn(model, messages)
                latency = int((time.time() - start) * 1000)
                records.append(
                    ResponseRecord(
                        run_id=run_id,
                        task_id=task.id,
                        model=model,
                        system_prompt=system_prompt,
                        messages=messages,
                        response=response,
                        latency_ms=latency,
                        usage=usage,
                    )
                )

                convo = list(messages) + [{"role": "assistant", "content": response}]
                for turn in task.follow_up_turns:
                    convo.append({"role": turn.role, "content": turn.content})
                    if turn.role != "user":
                        continue
                    start = time.time()
                    follow_up, usage = model_fn(model, convo)
                    latency = int((time.time() - start) * 1000)
                    convo.append({"role": "assistant", "content": follow_up})
                    records.append(
                        ResponseRecord(
                            run_id=run_id,
                            task_id=f"{task.id}@{len([t for t in convo if t['role']=='user'])-1}",
                            model=model,
                            system_prompt=system_prompt,
                            messages=list(convo),
                            response=follow_up,
                            latency_ms=latency,
                            usage=usage,
                        )
                    )
            else:
                messages = build_messages(task, system_prompt)
                if dry_run:
                    text, usage, latency = "[dry-run]", {}, None
                else:
                    start = time.time()
                    text, usage = model_fn(model, messages)
                    latency = int((time.time() - start) * 1000)
                records.append(
                    ResponseRecord(
                        run_id=run_id,
                        task_id=task.id,
                        model=model,
                        system_prompt=system_prompt,
                        messages=messages,
                        response=text,
                        latency_ms=latency,
                        usage=usage,
                    )
                )

    out = run_path / "responses.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(rec.model_dump_json() + "\n")

    return run_path
