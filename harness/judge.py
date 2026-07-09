from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from jinja2 import Template

from harness.providers import parse_spec, resolve_model_fn
from harness.schema import (
    ConsistencyResult,
    DoctrineSignature,
    Judgment,
    PairwiseDistance,
    Task,
    TaskFamily,
    apply_caps,
    compute_weighted_score,
)
from harness.tasks import load_task_map


class SelfJudgeError(RuntimeError):
    """Raised when the judge model is also a subject model in the run."""


def _load_template(name: str) -> Template:
    path = Path(__file__).resolve().parent.parent / "judges" / name
    return Template(path.read_text(encoding="utf-8"))


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Some models wrap or prepend prose; grab the outermost JSON object.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _render_transcript(messages: list[dict[str, str]]) -> str:
    """Human-readable USER/ASSISTANT transcript, system turn omitted."""
    lines = []
    for m in messages:
        role = m.get("role", "")
        if role == "system":
            continue
        lines.append(f"{role.upper()}: {m.get('content', '').strip()}")
    return "\n\n".join(lines)


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
        reference_answer=task.reference_answer.strip(),
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
    prior_turns: str = "",
) -> Judgment:
    prompt = render_rubric_prompt(task, response, prior_turns=prior_turns)
    messages = [
        {"role": "system", "content": "You grade Advaita Vedānta exam answers. Output JSON only."},
        {"role": "user", "content": prompt},
    ]

    if judge_fn is None:
        judge_fn = resolve_model_fn(judge_model)

    # Small/fast judges occasionally emit malformed JSON. Re-prompt a few times
    # before giving up so one bad reply doesn't discard the whole judgment.
    data = None
    last_err: Exception | None = None
    for _ in range(4):
        raw_text, _ = judge_fn(judge_model, messages)
        try:
            data = _extract_json(raw_text)
            break
        except (json.JSONDecodeError, ValueError) as err:
            last_err = err
    if data is None:
        raise ValueError(f"judge returned unparseable JSON after retries: {last_err}")

    dimension_scores = {
        k: int(v)
        for k, v in (data.get("dimension_scores") or {}).items()
        if k in task.rubric_dimensions
    }
    missing = [d for d in task.rubric_dimensions if d not in dimension_scores]
    if missing:
        # Absent dimensions score 0 in the weighted mean; surface it in the tag
        # list so it is not mistaken for a genuine zero the judge intended.
        print(f"    ~ {task.id}/{model}: judge omitted dimensions {missing}")

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
        provenance=task.provenance,
    )


def _assert_judge_independence(subject_models: set[str], judge_model: str) -> None:
    judge_id = parse_spec(judge_model)[1].lower()
    clashes = [m for m in subject_models if parse_spec(m)[1].lower() == judge_id]
    if clashes:
        raise SelfJudgeError(
            f"Judge model '{judge_model}' also appears as a subject model "
            f"({clashes}). LLM judges self-prefer; use a distinct judge or pass "
            f"--allow-self-judge to override (results are not publication-grade)."
        )


def judge_run(
    run_dir: Path,
    tasks_dir: Path,
    judge_model: str,
    dry_run: bool = False,
    allow_self_judge: bool = False,
) -> Path:
    task_map = load_task_map(tasks_dir)
    responses_path = run_dir / "responses.jsonl"
    judged_path = run_dir / "judged.jsonl"

    # Group every response record under its base task id (strips the @N
    # multi-turn suffix). Keeping full records — not just response strings —
    # lets us rebuild the conversation the judge must see.
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    subject_models: set[str] = set()
    with responses_path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            base_id = rec["task_id"].split("@")[0]
            grouped[(rec["model"], base_id)].append(rec)
            subject_models.add(rec["model"])

    if not dry_run and not allow_self_judge:
        _assert_judge_independence(subject_models, judge_model)

    judge_fn = None if dry_run else resolve_model_fn(judge_model)
    judgments: list[Judgment] = []
    skipped: list[tuple[str, str]] = []

    # Write each judgment as it is produced so a mid-run failure never discards
    # completed work (the whole pass died once on a single malformed reply).
    with judged_path.open("w", encoding="utf-8") as jf:
        for (model, base_id), records in grouped.items():
            task = task_map.get(base_id)
            if not task:
                continue

            if dry_run:
                j = Judgment(
                    task_id=base_id, model=model, judge_model=judge_model,
                    dimension_scores={d: 2 for d in task.rubric_dimensions},
                    rationale="[dry-run]", raw_score=50.0, final_score=50.0,
                    provenance=task.provenance,
                )
            else:
                try:
                    if len(records) > 1:
                        # Multi-turn pressure dialogue (misconception_repair,
                        # sustained_dialectic): judge sees the whole transcript.
                        # The record with the most messages carries the whole
                        # dialogue; its `response` is the final assistant turn.
                        final = max(records, key=lambda r: len(r["messages"]))
                        prior = _render_transcript(final["messages"])
                        j = judge_response(task, final["response"], model, judge_model,
                                           judge_fn=judge_fn, prior_turns=prior)
                    else:
                        j = judge_response(task, records[0]["response"], model, judge_model,
                                           judge_fn=judge_fn)
                except Exception as exc:  # noqa: BLE001 - one bad judgment must not sink the run
                    skipped.append((model, base_id))
                    print(f"    ! judge skipped {model}/{base_id}: {exc}")
                    continue

            judgments.append(j)
            jf.write(j.model_dump_json() + "\n")
            jf.flush()

    if skipped:
        print(f"    judge skipped {len(skipped)} task(s) after retries")

    if not dry_run:
        _judge_consistency(run_dir, task_map, judgments, judge_model, judge_fn)

    return judged_path


def _judge_consistency(run_dir, task_map, judgments, judge_model, judge_fn) -> Path | None:
    """Score consistency-family variant groups at the group level.

    Per-variant rubric scores alone cannot express doctrine drift — that is a
    property *across* the group. This second judge compares the doctrine
    signatures of every variant and returns a pairwise distance.
    """
    tmpl = _load_template("consistency_judge.txt")

    # (model, variant_group_id) -> [(task_id, Judgment)]
    groups: dict[tuple[str, str], list[Judgment]] = defaultdict(list)
    for j in judgments:
        task = task_map.get(j.task_id)
        if task and task.family == TaskFamily.CONSISTENCY_ADVERSARIAL and task.variant_group_id:
            groups[(j.model, task.variant_group_id)].append(j)

    if not groups:
        return None

    results: list[ConsistencyResult] = []
    for (model, group_id), members in groups.items():
        if len(members) < 2:
            continue
        gold_key = next(
            (task_map[m.task_id].gold_doctrine_key for m in members
             if task_map.get(m.task_id) and task_map[m.task_id].gold_doctrine_key),
            "",
        )
        variants_json = json.dumps([
            {
                "task_id": m.task_id,
                "final_score": round(m.final_score, 1),
                "doctrine_signature": m.doctrine_signature.model_dump(),
            }
            for m in members
        ], ensure_ascii=False, indent=2)

        prompt = tmpl.render(
            variant_group_id=group_id, gold_doctrine_key=gold_key, variants_json=variants_json
        )
        data = None
        for _ in range(4):
            raw_text, _ = judge_fn(judge_model, [
                {"role": "system", "content": "You compare Advaita doctrine signatures. Output JSON only."},
                {"role": "user", "content": prompt},
            ])
            try:
                data = _extract_json(raw_text)
                break
            except (json.JSONDecodeError, ValueError):
                pass
        if data is None:
            print(f"    ! consistency judge skipped {model}/{group_id}: unparseable JSON")
            continue

        pairwise = [
            PairwiseDistance(a=p.get("a", ""), b=p.get("b", ""),
                             distance=int(p.get("distance", 0)), note=p.get("note", ""))
            for p in (data.get("pairwise_distances") or [])
        ]
        max_distance = int(data.get("max_distance", max((p.distance for p in pairwise), default=0)))
        # Recompute from distance for determinism rather than trusting the
        # judge's own arithmetic.
        consistency_score = 100.0 * (1 - max_distance / 3.0)
        mean_variant = sum(m.final_score for m in members) / len(members)
        group_score = 0.6 * consistency_score + 0.4 * mean_variant

        results.append(ConsistencyResult(
            variant_group_id=group_id, model=model, judge_model=judge_model,
            member_task_ids=[m.task_id for m in members], pairwise_distances=pairwise,
            max_distance=max_distance, consistency_score=round(consistency_score, 2),
            mean_variant_score=round(mean_variant, 2), group_score=round(group_score, 2),
            drift_flags=list(data.get("drift_flags") or []), summary=data.get("summary", ""),
        ))

    out = run_dir / "consistency.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(r.model_dump_json() + "\n")
    return out
