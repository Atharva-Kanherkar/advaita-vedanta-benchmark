"""Provider routing for AdvaitaBench.

One model spec, one call site, many backends. The routing rule encodes a
billing decision, not just an API-shape decision:

- **Direct providers** (OpenAI, Anthropic, Google) are called on their native
  endpoints so the run draws on first-party credits.
- **Everything else** (xAI/Grok, DeepSeek, Qwen, GLM, Kimi, Llama, Mistral, …)
  routes through **OpenRouter**, which is real out-of-pocket spend.

A spec may name its route explicitly as ``provider:model_id`` (e.g.
``openrouter:anthropic/claude-3.5-sonnet`` forces OpenRouter even for a Claude
model). A bare id is routed by prefix. OpenAI, Google, and OpenRouter all speak
the OpenAI Chat Completions shape, so they share one client factory; Anthropic
uses its own SDK.
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable

# (text, usage) where usage carries token counts and, when the backend reports
# it (OpenRouter does), a real dollar `cost`.
ModelFn = Callable[[str, list[dict[str, str]]], tuple[str, dict[str, Any]]]

DIRECT_PROVIDERS = {"openai", "anthropic", "google"}
ALL_PROVIDERS = DIRECT_PROVIDERS | {"openrouter"}

# OpenAI-compatible endpoints (base_url, env var holding the key).
_OPENAI_COMPAT = {
    "openai": (None, "OPENAI_API_KEY"),
    "google": ("https://generativelanguage.googleapis.com/v1beta/openai/", "GEMINI_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
}

_MAX_RETRIES = 4
_BACKOFF_BASE = 2.0


def infer_provider(model_id: str) -> str:
    """Route a bare model id to a provider by prefix. Unknown -> OpenRouter."""
    m = model_id.lower()
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith(("gpt", "o1", "o3", "o4", "chatgpt", "text-", "davinci")):
        return "openai"
    if m.startswith(("gemini", "models/gemini")):
        return "google"
    return "openrouter"


def parse_spec(spec: str) -> tuple[str, str]:
    """Return (provider, model_id) for a spec.

    ``openai:gpt-4.1`` -> ("openai", "gpt-4.1").
    ``x-ai/grok-3`` -> ("openrouter", "x-ai/grok-3") by inference.
    A leading ``provider:`` is only honored for known providers so that
    OpenRouter ids containing ``:`` (e.g. ``deepseek/deepseek-r1:free``) are not
    mis-parsed.
    """
    if ":" in spec:
        head, rest = spec.split(":", 1)
        if head.lower() in ALL_PROVIDERS:
            return head.lower(), rest
    return infer_provider(spec), spec


def uses_real_money(spec: str) -> bool:
    """True if calling this spec spends OpenRouter balance (out of pocket)."""
    return parse_spec(spec)[0] == "openrouter"


def _key(env_var: str, provider: str) -> str:
    key = os.environ.get(env_var)
    if not key and provider == "google":
        key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            f"Missing API key for provider '{provider}': set ${env_var}."
        )
    return key


def _retryable(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(
        s in text
        for s in ("rate", "timeout", "timed out", "overloaded", "503", "502", "500", "529",
                  "connection", "temporarily")
    )


def _with_retries(fn: Callable[[], tuple[str, dict[str, Any]]]) -> tuple[str, dict[str, Any]]:
    last: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - normalized across SDKs
            last = exc
            if attempt == _MAX_RETRIES - 1 or not _retryable(exc):
                raise
            time.sleep(_BACKOFF_BASE**attempt)
    raise last  # pragma: no cover


def _openai_compat_fn(provider: str, model_id: str) -> ModelFn:
    from openai import OpenAI

    base_url, env_var = _OPENAI_COMPAT[provider]
    kwargs: dict[str, Any] = {"api_key": _key(env_var, provider)}
    if base_url:
        kwargs["base_url"] = base_url
    if provider == "openrouter":
        # Referer/title are OpenRouter conventions for attributing traffic.
        kwargs["default_headers"] = {
            "HTTP-Referer": "https://github.com/Atharva-Kanherkar/advaita-vedanta-benchmark",
            "X-Title": "AdvaitaBench",
        }
    client = OpenAI(**kwargs)

    def call(_spec: str, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
        def once(include_temp: bool) -> tuple[str, dict[str, Any]]:
            params: dict[str, Any] = {"model": model_id, "messages": messages}
            if include_temp:
                params["temperature"] = 0
            if provider == "openrouter":
                # Ask OpenRouter to report the actual dollar cost of the call.
                params["extra_body"] = {"usage": {"include": True}}
            resp = client.chat.completions.create(**params)
            text = resp.choices[0].message.content or ""
            usage: dict[str, Any] = {}
            if resp.usage:
                usage = {
                    "input_tokens": getattr(resp.usage, "prompt_tokens", 0),
                    "output_tokens": getattr(resp.usage, "completion_tokens", 0),
                }
                cost = getattr(resp.usage, "cost", None)
                if cost is not None:
                    usage["cost_usd"] = float(cost)
            return text, usage

        try:
            return _with_retries(lambda: once(True))
        except Exception as exc:  # noqa: BLE001
            # Reasoning models (o-series and some others) reject temperature.
            if "temperature" in str(exc).lower():
                return _with_retries(lambda: once(False))
            raise

    return call


def _anthropic_fn(model_id: str) -> ModelFn:
    from anthropic import Anthropic

    client = Anthropic(api_key=_key("ANTHROPIC_API_KEY", "anthropic"))

    def call(_spec: str, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
        system = ""
        chat: list[dict[str, str]] = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                chat.append(m)

        def once() -> tuple[str, dict[str, Any]]:
            resp = client.messages.create(
                model=model_id,
                max_tokens=4096,
                system=system,
                messages=chat,
                temperature=0,
            )
            text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
            usage = {
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
            }
            return text, usage

        return _with_retries(once)

    return call


def resolve_model_fn(spec: str) -> ModelFn:
    """Build a callable for a model spec, routed to the right backend."""
    provider, model_id = parse_spec(spec)
    if provider == "anthropic":
        return _anthropic_fn(model_id)
    if provider in _OPENAI_COMPAT:
        return _openai_compat_fn(provider, model_id)
    raise ValueError(f"Unknown provider '{provider}' in spec '{spec}'")
