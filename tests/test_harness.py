"""Offline tests for the AdvaitaBench harness — no network, no API keys.

Focus on the behaviors that are easy to break silently: score caps, provider
routing, multi-turn transcript reconstruction, and consistency-group scoring.
"""

from __future__ import annotations

import json

import harness.judge as judge_mod
from harness.providers import infer_provider, parse_spec, uses_real_money
from harness.registry import expand_models
from harness.schema import Task, TaskFamily, apply_caps, compute_weighted_score


def _task(**kw) -> Task:
    base = dict(
        id="t-001", family=TaskFamily.LEVEL_OF_REALITY, prompt="p",
        rubric_dimensions=["level_identification", "non_contradiction",
                           "vyavahara_respect", "paramartha_precision"],
    )
    base.update(kw)
    return Task(**base)


# --- caps -------------------------------------------------------------------

def test_school_mixing_caps_any_family():
    t = _task(family=TaskFamily.CONCEPT_PRECISION,
              rubric_dimensions=["term_accuracy", "distinction_clarity"])
    final, capped, reason = apply_caps(t, 95.0, ["school_mixing"], {"term_accuracy": 4})
    assert capped and final == 30.0 and reason == "school_mixing"


def test_level_collapse_caps_misconception_repair():
    t = _task(family=TaskFamily.MISCONCEPTION_REPAIR,
              rubric_dimensions=["misconception_identified", "correction_quality"])
    final, capped, _ = apply_caps(t, 90.0, ["level_collapse"], {})
    assert capped and final == 25.0


def test_text_ungrounded_only_caps_text_grounded():
    t = _task(family=TaskFamily.LEVEL_OF_REALITY)
    final, capped, _ = apply_caps(t, 88.0, ["text_ungrounded"], {})
    assert not capped and final == 88.0


def test_tightest_cap_wins():
    t = _task(family=TaskFamily.SCHOOL_DISCRIMINATION,
              rubric_dimensions=["advaita_position"])
    final, _, reason = apply_caps(t, 99.0, ["school_mixing", "new_age_nonduality"], {})
    assert final == 30.0 and reason == "school_mixing"


def test_weighted_score_uniform_default():
    t = _task()
    assert compute_weighted_score(t, {d: 4 for d in t.rubric_dimensions}) == 100.0
    assert compute_weighted_score(t, {d: 2 for d in t.rubric_dimensions}) == 50.0


# --- provider routing -------------------------------------------------------

def test_routing_direct_vs_openrouter():
    assert infer_provider("claude-sonnet-4-5") == "anthropic"
    assert infer_provider("gpt-4.1") == "openai"
    assert infer_provider("o3-mini") == "openai"
    assert infer_provider("gemini-2.5-pro") == "google"
    assert infer_provider("x-ai/grok-3") == "openrouter"
    assert infer_provider("deepseek/deepseek-r1") == "openrouter"


def test_explicit_provider_prefix_forces_route():
    assert parse_spec("openrouter:anthropic/claude-3.5-sonnet") == (
        "openrouter", "anthropic/claude-3.5-sonnet")
    assert parse_spec("openai:gpt-4.1") == ("openai", "gpt-4.1")
    # A colon inside an OpenRouter id must not be mistaken for a provider prefix.
    assert parse_spec("deepseek/deepseek-r1:free") == (
        "openrouter", "deepseek/deepseek-r1:free")


def test_uses_real_money():
    assert uses_real_money("x-ai/grok-3")
    assert not uses_real_money("anthropic:claude-sonnet-4-5")
    assert not uses_real_money("gpt-4.1")


def test_registry_expand():
    reg = {"groups": {"a": ["m1", "m2"], "b": ["m2", "m3"]}}
    assert expand_models("@all", reg) == ["m1", "m2", "m3"]  # de-duped, ordered
    assert expand_models("@a,m4", reg) == ["m1", "m2", "m4"]


# --- multi-turn judging (the headline fix) ---------------------------------

class _FakeJudge:
    """Records the rubric prompt it saw; returns canned JSON per judge type."""

    def __init__(self):
        self.rubric_prompts = []

    def __call__(self, _model, messages):
        user = messages[-1]["content"]
        if "compare" in messages[0]["content"].lower():
            return json.dumps({
                "pairwise_distances": [{"a": "ca-001a", "b": "ca-001b", "distance": 2}],
                "max_distance": 2, "drift_flags": ["doctrine_drift"], "summary": "drift",
            }), {}
        self.rubric_prompts.append(user)
        # Score every known dimension 3; judge_response filters to the task's own.
        dims = ["misconception_identified", "correction_quality", "dialogue_stability",
                "pedagogical_tone", "doctrine_consistency", "robustness_to_framing",
                "terminology_invariance", "adversarial_integrity"]
        return json.dumps({
            "dimension_scores": {d: 3 for d in dims},
            "failure_tags": [], "rationale": "ok",
            "doctrine_signature": {"core_claim": "c", "levels_used": ["vyavaharika"],
                                   "school": "advaita", "key_distinctions": []},
        }), {}


def _write_multiturn_responses(run_dir):
    sysmsg = {"role": "system", "content": "sp"}
    q0 = {"role": "user", "content": "If all is Brahman, ignore morality?"}
    a0 = "No — vyavaharika ethics bind under avidya."
    q1 = {"role": "user", "content": "But the world is unreal, so who cares?"}
    a1 = "Mithya is not tuccha; karma-phala operates."
    recs = [
        {"run_id": "r", "task_id": "mr-001", "model": "m", "system_prompt": "sp",
         "messages": [sysmsg, q0], "response": a0, "usage": {}},
        {"run_id": "r", "task_id": "mr-001@1", "model": "m", "system_prompt": "sp",
         "messages": [sysmsg, q0, {"role": "assistant", "content": a0}, q1],
         "response": a1, "usage": {}},
    ]
    (run_dir / "responses.jsonl").write_text(
        "\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")


def test_multiturn_judge_sees_full_transcript(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "mr.yaml").write_text(
        "id: mr-001\nfamily: misconception_repair\nprompt: q\n"
        "rubric_dimensions: [misconception_identified, correction_quality, "
        "dialogue_stability, pedagogical_tone]\n"
        "follow_up_turns:\n  - role: user\n    content: pushback\n"
        "gold_points: [g]\n",
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_multiturn_responses(run_dir)

    fake = _FakeJudge()
    monkeypatch.setattr(judge_mod, "resolve_model_fn", lambda _m: fake)

    judge_mod.judge_run(run_dir, tasks_dir, "judge-x", allow_self_judge=False)

    assert len(fake.rubric_prompts) == 1
    prompt = fake.rubric_prompts[0]
    # The judge must see BOTH the user's pushback AND the model's first answer,
    # i.e. the whole dialogue — that is exactly what the old code dropped.
    assert "ignore morality" in prompt
    assert "But the world is unreal" in prompt
    assert "vyavaharika ethics bind" in prompt


def test_consistency_group_scoring(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "ca.yaml").write_text(
        "id: ca-001a\nfamily: consistency_adversarial\nvariant_group_id: ca-001\n"
        "gold_doctrine_key: k\nprompt: q\n"
        "rubric_dimensions: [doctrine_consistency, robustness_to_framing, "
        "terminology_invariance, adversarial_integrity]\n"
        "---\n"
        "id: ca-001b\nfamily: consistency_adversarial\nvariant_group_id: ca-001\n"
        "gold_doctrine_key: k\nprompt: q\n"
        "rubric_dimensions: [doctrine_consistency, robustness_to_framing, "
        "terminology_invariance, adversarial_integrity]\n",
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    recs = [
        {"run_id": "r", "task_id": tid, "model": "m", "system_prompt": "sp",
         "messages": [{"role": "user", "content": "q"}], "response": "ans", "usage": {}}
        for tid in ("ca-001a", "ca-001b")
    ]
    (run_dir / "responses.jsonl").write_text(
        "\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")

    monkeypatch.setattr(judge_mod, "resolve_model_fn", lambda _m: _FakeJudge())
    judge_mod.judge_run(run_dir, tasks_dir, "judge-x")

    lines = (run_dir / "consistency.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    result = json.loads(lines[0])
    # max_distance 2 -> consistency 100*(1-2/3) = 33.33; each variant scored 75
    # (all dims 3). group = 0.6*33.33 + 0.4*75 = 50.0.
    assert result["max_distance"] == 2
    assert abs(result["consistency_score"] - 33.33) < 0.1
    assert abs(result["group_score"] - 50.0) < 0.2
