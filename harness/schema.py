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
    OPEN_ELICITATION = "open_elicitation"
    SUSTAINED_DIALECTIC = "sustained_dialectic"


class Turn(BaseModel):
    role: str
    content: str


class Passage(BaseModel):
    text: str
    source: str = ""
    tier: str = "B"


# How a task's content relates to widely-available training data. Reported
# stratified so the canonical-vs-novel gap is visible (memorization control).
PROVENANCE_VALUES = ("canonical", "paraphrased", "novel")


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
    # Full prose reference answer the judge grades against (not quoted back).
    # Strongly preferred over gold_points alone: it turns judging into
    # verification-against-reference rather than generation-from-prior.
    reference_answer: str = ""
    failure_tags_watch: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    difficulty: str = "pilot"
    provenance: str = "canonical"


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
    provenance: str = "canonical"


class PairwiseDistance(BaseModel):
    a: str
    b: str
    distance: int
    note: str = ""


class ConsistencyResult(BaseModel):
    variant_group_id: str
    model: str
    judge_model: str
    member_task_ids: list[str] = Field(default_factory=list)
    pairwise_distances: list[PairwiseDistance] = Field(default_factory=list)
    max_distance: int = 0
    consistency_score: float = 0.0
    mean_variant_score: float = 0.0
    group_score: float = 0.0
    drift_flags: list[str] = Field(default_factory=list)
    summary: str = ""


FAMILY_WEIGHTS: dict[str, float] = {
    "concept_precision": 0.13,
    "level_of_reality": 0.16,
    "school_discrimination": 0.16,
    "text_grounded": 0.16,
    "misconception_repair": 0.12,
    "consistency_adversarial": 0.07,
    "open_elicitation": 0.09,
    "sustained_dialectic": 0.11,
}

# tag -> (families it caps, cap value). "*" means the cap applies in every
# family. A doctrine that mixes schools or dissolves into New Age vagueness is
# a failure regardless of which surface the task was probing, so those two are
# global. Level collapse / nihilistic denial cap wherever levels are in play.
_ALL = "*"
TAG_CAPS: dict[str, tuple[object, float]] = {
    "school_mixing": (_ALL, 30.0),
    "new_age_nonduality": (_ALL, 35.0),
    "level_collapse": ({"level_of_reality", "misconception_repair", "sustained_dialectic"}, 25.0),
    "nihilistic_denial": ({"level_of_reality", "misconception_repair", "sustained_dialectic"}, 25.0),
    "text_ungrounded": ({"text_grounded"}, 20.0),
    # Capitulating under pressure defeats the whole point of the pressure families.
    "sycophantic_agreement": ({"misconception_repair", "sustained_dialectic"}, 30.0),
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


def apply_caps(
    task: Task, raw: float, failure_tags: list[str], dimension_scores: dict[str, int]
) -> tuple[float, bool, str | None]:
    cap: float | None = None
    reason: str | None = None

    def tighten(candidate: float, why: str) -> None:
        nonlocal cap, reason
        if cap is None or candidate < cap:
            cap, reason = candidate, why

    # A core term scored wrong hard-caps a concept-precision task.
    if task.family == TaskFamily.CONCEPT_PRECISION and dimension_scores.get("term_accuracy", 4) <= 1:
        tighten(40.0, "term_accuracy <= 1")

    for tag in failure_tags:
        spec = TAG_CAPS.get(tag)
        if not spec:
            continue
        families, tag_cap = spec
        if families == _ALL or task.family.value in families:
            tighten(tag_cap, tag)

    if cap is not None:
        return min(raw, cap), True, reason
    return raw, False, None
