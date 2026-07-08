"""Model-registry expansion for the `--models` flag.

A `--models` value is a comma list where each element is one of:
- a literal model spec (``anthropic:claude-sonnet-4-5``, ``x-ai/grok-3``)
- ``@group`` — expands to the named group in config/models.yaml
- ``@all`` — expands to every model across all groups (de-duplicated)
"""

from __future__ import annotations

from pathlib import Path

import yaml

DEFAULT_REGISTRY = Path(__file__).resolve().parent.parent / "config" / "models.yaml"


def load_registry(path: Path | None = None) -> dict:
    path = path or DEFAULT_REGISTRY
    if not path.exists():
        return {"groups": {}, "judge": None}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def expand_models(value: str, registry: dict | None = None) -> list[str]:
    reg = registry if registry is not None else load_registry()
    groups: dict[str, list[str]] = reg.get("groups") or {}

    out: list[str] = []
    for raw in value.split(","):
        token = raw.strip()
        if not token:
            continue
        if token == "@all":
            for members in groups.values():
                out.extend(members)
        elif token.startswith("@"):
            name = token[1:]
            if name not in groups:
                raise ValueError(
                    f"Unknown model group '@{name}'. Known: {sorted(groups)}"
                )
            out.extend(groups[name])
        else:
            out.append(token)

    # De-duplicate while preserving order.
    seen: set[str] = set()
    deduped = []
    for m in out:
        if m not in seen:
            seen.add(m)
            deduped.append(m)
    return deduped


def default_judge(registry: dict | None = None) -> str | None:
    reg = registry if registry is not None else load_registry()
    return reg.get("judge")
