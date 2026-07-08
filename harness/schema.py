from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskFamily(str, Enum):
    CONCEPT_PRECISION = "concept_precision"
    LEVEL_OF_REALITY = "level_of_reality"
    SCHOOL_DISCRIMINATION = "school_discrimination"
    TEXT_GROUNDED = "text_grounded"
    MISCONCEPTION_REPAIR = "misconception_repair"
    CONSISTENCY_ADVERSARIAL = "consistency_adversarial"


class Turn(BaseModel):
    role: str
    content: str


class Passage(BaseModel):
    text: str
    source: str = ""
    tier: str = "B"


class Task(BaseModel):
    id: str
    family: TaskFamily
    prompt: str
    turns: list[Turn] = Field(default_factory=list)
    follow_up_turns: list[Turn] = Field(default_factory=list)
    passage: Passage | None = None
    variant_group_id: str | None = None
    gold_doctrine_key: str | None = None
    target_school: str = "advaita"
    contrast_school: str | None = None
    language: str = "en"
    rubric_dimensions: list[str]
    dimension_weights: dict[str, float] = Field(default_factory=dict)
    gold_points: list[str] = Field(default_factory=list)
    required_distinctions: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
    failure_tags_watch: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    difficulty: str = "pilot"


class ResponseRecord(BaseModel):
    run_id: str
    task_id: str
    model: str
    system_prompt: str
    messages: list[dict[str, str]]
    response: str
    latency_ms: int | None = None
    usage: dict[str, Any] = Field(default_factory=dict)


class DoctrineSignature(BaseModel):
    core_claim: str = ""
    levels_used: list[str] = Field(default_factory=list)
    school: str = "advaita"
    key_distinctions: list[str] = Field(default_factory=list)


class Judgment(BaseModel):
    task_id: str
    model: str
    judge_model: str
    dimension_scores: dict[str, int]
    failure_tags: list[str] = Field(default_factory=list)
    rationale: str = ""
    doctrine_signature: DoctrineSignature = Field(default_factory=DoctrineSignature)
    raw_score: float = 0.0
    final_score: float = 0.0
    capped: bool = False
    cap_reason: str | None = None


FAMILY_WEIGHTS: dict[str, float] = {
    "concept_precision": 0.15,
    "level_of_reality": 0.20,
    "school_discrimination": 0.20,
    "text_grounded": 0.20,
    "misconception_repair": 0.15,
    "consistency_adversarial": 0.10,
}

SCORE_CAPS: dict[str, tuple[str, float]] = {
    "school_mixing": ("school_discrimination", 30.0),
    "level_collapse": ("level_of_reality", 25.0),
    "nihilistic_denial": ("level_of_reality", 25.0),
    "text_ungrounded": ("text_grounded", 20.0),
    "new_age_nonduality": ("school_discrimination", 35.0),
}


def compute_weighted_score(task: Task, dimension_scores: dict[str, int]) -> float:
    weights = task.dimension_weights or {
        dim: 1.0 / len(task.rubric_dimensions) for dim in task.rubric_dimensions
    }
    total_w = sum(weights.get(d, 0) for d in task.rubric_dimensions)
    if total_w == 0:
        return 0.0
    weighted = sum(weights.get(d, 0) * dimension_scores.get(d, 0) for d in task.rubric_dimensions)
    return 100.0 * weighted / (4.0 * total_w)


def apply_caps(task: Task, raw: float, failure_tags: list[str], dimension_scores: dict[str, int]) -> tuple[float, bool, str | None]:
    cap: float | None = None
    reason: str | None = None

    if task.family == TaskFamily.CONCEPT_PRECISION and any(
        dimension_scores.get("term_accuracy", 4) <= 1 for _ in [0]
    ):
        if dimension_scores.get("term_accuracy", 4) <= 1:
            cap = 40.0
            reason = "term_accuracy <= 1"

    for tag in failure_tags:
        if tag in SCORE_CAPS:
            family, tag_cap = SCORE_CAPS[tag]
            if task.family.value == family or tag in ("school_mixing", "new_age_nonduality"):
                cap = min(cap, tag_cap) if cap else tag_cap
                reason = reason or tag

    if cap is not None:
        return min(raw, cap), True, reason
    return raw, False, None
