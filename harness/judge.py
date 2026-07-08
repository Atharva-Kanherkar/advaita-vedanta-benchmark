from __future__ import annotations

import json
import re
from pathlib import Path

from jinja2 import Template

from harness.runner import resolve_model_fn
from harness.schema import (
    DoctrineSignature,
    Judgment,
    Task,
    apply_caps,
    compute_weighted_score,
)
from harness.tasks import load_task_map


def _load_template(name: str) -> Template:
    path = Path(__file__).resolve().parent.parent / "judges" / name
    return Template(path.read_text(encoding="utf-8"))


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text)


def render_rubric_prompt(task: Task, response: str, prior_turns: str = "") -> str:
    tmpl = _load_template("rubric_judge.txt")
    passage_text = passage_source = passage_tier = ""
    if task.passage:
        passage_text = task.passage.text
        passage_source = task.passage.source
        passage_tier = task.passage.tier

    return tmpl.render(
        family=task.family.value,
        task_id=task.id,
        target_school=task.target_school,
        prompt=task.prompt,
        passage=bool(task.passage),
        passage_text=passage_text,
        passage_source=passage_source,
        passage_tier=passage_tier,
        prior_turns=prior_turns,
        response=response,
        rubric_dimensions="\n".join(f"- {d}" for d in task.rubric_dimensions),
        gold_points="\n".join(f"- {g}" for g in task.gold_points) or "(none)",
        required_distinctions="\n".join(f"- {r}" for r in task.required_distinctions) or "(none)",
        forbidden_claims="\n".join(f"- {f}" for f in task.forbidden_claims) or "(none)",
    )


def judge_response(
    task: Task,
    response: str,
    model: str,
    judge_model: str,
    judge_fn=None,
) -> Judgment:
    prompt = render_rubric_prompt(task, response)
    messages = [
        {"role": "system", "content": "You grade Advaita Vedānta exam answers. Output JSON only."},
        {"role": "user", "content": prompt},
    ]

    if judge_fn is None:
        judge_fn = resolve_model_fn(judge_model)

    raw_text, _ = judge_fn(judge_model, messages)
    data = _extract_json(raw_text)

    dimension_scores = {k: int(v) for k, v in data.get("dimension_scores", {}).items()}
    failure_tags = list(data.get("failure_tags") or [])
    sig = data.get("doctrine_signature") or {}

    raw_score = compute_weighted_score(task, dimension_scores)
    final_score, capped, cap_reason = apply_caps(task, raw_score, failure_tags, dimension_scores)

    return Judgment(
        task_id=task.id,
        model=model,
        judge_model=judge_model,
        dimension_scores=dimension_scores,
        failure_tags=failure_tags,
        rationale=data.get("rationale", ""),
        doctrine_signature=DoctrineSignature(
            core_claim=sig.get("core_claim", ""),
            levels_used=sig.get("levels_used") or [],
            school=sig.get("school", "advaita"),
            key_distinctions=sig.get("key_distinctions") or [],
        ),
        raw_score=raw_score,
        final_score=final_score,
        capped=capped,
        cap_reason=cap_reason,
    )


def judge_run(
    run_dir: Path,
    tasks_dir: Path,
    judge_model: str,
    dry_run: bool = False,
) -> Path:
    task_map = load_task_map(tasks_dir)
    responses_path = run_dir / "responses.jsonl"
    judged_path = run_dir / "judged.jsonl"

    # Group misconception repair follow-ups under base task id
    grouped: dict[tuple[str, str], list[str]] = {}
    meta: dict[tuple[str, str], dict] = {}

    with responses_path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            base_id = rec["task_id"].split("@")[0]
            key = (rec["model"], base_id)
            grouped.setdefault(key, []).append(rec["response"])
            meta[key] = rec

    judge_fn = None if dry_run else resolve_model_fn(judge_model)
    judgments: list[Judgment] = []

    for (model, base_id), responses in grouped.items():
        task = task_map.get(base_id)
        if not task:
            continue

        if dry_run:
            dim_scores = {d: 2 for d in task.rubric_dimensions}
            j = Judgment(
                task_id=base_id,
                model=model,
                judge_model=judge_model,
                dimension_scores=dim_scores,
                rationale="[dry-run]",
                raw_score=50.0,
                final_score=50.0,
            )
        else:
            combined = "\n\n---\n\n".join(
                f"Turn {i+1}:\n{r}" for i, r in enumerate(responses)
            )
            j = judge_response(task, combined, model, judge_model, judge_fn=judge_fn)

        judgments.append(j)

    with judged_path.open("w", encoding="utf-8") as f:
        for j in judgments:
            f.write(j.model_dump_json() + "\n")

    return judged_path
