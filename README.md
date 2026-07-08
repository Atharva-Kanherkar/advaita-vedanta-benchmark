# AdvaitaBench

Research-grade benchmark for **Advaita Vedānta doctrinal competence** in large language models.

AdvaitaBench tests whether models can teach classical Advaita without conflating schools, collapsing levels of reality, or reproducing popular misconceptions. It is not a general Hinduism quiz or a “spiritual vibes” eval.

## Six task families

| Family | What it tests |
|--------|----------------|
| **Concept precision** | Brahman, Ātman, jīva, māyā, avidyā, sākṣī, upādhi, mithyā, … |
| **Level-of-reality reasoning** | paramārthika / vyāvahārika / prātibhāsika without contradiction |
| **School discrimination** | No Dvaita/Buddhist/Yoga/New Age mixing |
| **Text-grounded interpretation** | Claims justified from supplied passages |
| **Misconception repair** | Multi-turn correction of common distortions |
| **Consistency & adversarial robustness** | Same doctrine under rephrasing and hostility |

## Documentation

- [Methodology](docs/METHODOLOGY.md) — research design, validity, publication checklist
- [Rubrics](docs/RUBRICS.md) — per-family scoring dimensions and caps
- [Judging](docs/JUDGING.md) — judge protocol, human adjudication, reproducibility

## Quick start

Requires Python ≥ 3.11.

```bash
cd ~/Projects/advaita-vedanta-benchmark
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

advaita-bench validate          # validate seed tasks
python -m pytest tests/ -q      # offline harness tests (no API keys)
advaita-bench models            # show the model registry

# Dry-run the whole pipeline (no API calls)
advaita-bench run --models @smoke --dry-run
advaita-bench judge --run runs/<run_id> --dry-run
advaita-bench report --run runs/<run_id>

# Live run — see provider/keys below
advaita-bench run --models @frontier,@openrouter
advaita-bench judge --run runs/<run_id>          # judge from config/models.yaml
advaita-bench report --run runs/<run_id>
```

### Providers and keys

Models route by provider — which is also a billing choice:

| Provider | Route | Key |
|----------|-------|-----|
| OpenAI (`gpt-*`, `o*`) | direct | `OPENAI_API_KEY` |
| Anthropic (`claude-*`) | direct | `ANTHROPIC_API_KEY` |
| Google (`gemini-*`) | direct | `GEMINI_API_KEY` |
| everything else (Grok, DeepSeek, Qwen, GLM, Kimi, …) | **OpenRouter** (real $) | `OPENROUTER_API_KEY` |

Force a route with a `provider:` prefix (`openrouter:anthropic/claude-3.5-sonnet`).
Model sets live in [`config/models.yaml`](config/models.yaml); `@frontier`,
`@openrouter`, `@smoke`, `@all` expand there. Each run records provider routing,
token usage, and OpenRouter dollar cost in `manifest.json`. The judge model must
differ from every subject model (enforced).

### Corpus

```bash
python -m scripts.fetch_corpus          # fetch + hash held-out source passages
```

See [corpus/SOURCES.md](corpus/SOURCES.md) for sources and licensing.

## Project structure

```
docs/           Methodology, rubrics, judging spec
tasks/          YAML task bank (pilot: ~20 seed tasks)
judges/         LLM judge prompt templates
harness/        Python package (providers → run → judge → report)
config/         Family weights, run settings, model registry
corpus/         Source-text manifest + fetch script (raw/ gitignored)
tests/          Offline harness tests (no API keys)
runs/           Output artifacts (gitignored)
```

## Pilot status

Current task bank is a **pilot seed set** (3–4 tasks per family). Publication requires:

- ≥30 tasks per family
- Human adjudication (κ ≥ 0.65)
- ≥3 subject models + distinct judge model
- Full failure analysis appendix

## Scope

**In scope:** Classical Advaita (Śaṅkara tradition), doctrinal precision, pedagogy under pressure.

**Out of scope:** Spiritual attainment, guru authentication, caste/politics, non-Advaita schools except where contrast is explicit.

## License

MIT (suggested — update if you prefer another license)
