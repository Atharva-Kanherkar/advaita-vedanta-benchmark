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

```bash
cd ~/Projects/advaita-vedanta-benchmark
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Validate seed tasks
advaita-bench validate

# Dry-run harness (no API calls)
advaita-bench run --models gpt-4.1 --dry-run
advaita-bench judge --run runs/<run_id> --dry-run
advaita-bench report --run runs/<run_id>

# Live run (requires OPENAI_API_KEY and/or ANTHROPIC_API_KEY)
advaita-bench run --models gpt-4.1,claude-sonnet-4-20250514
advaita-bench judge --run runs/<run_id> --judge-model gpt-4.1
advaita-bench report --run runs/<run_id>
```

## Project structure

```
docs/           Methodology, rubrics, judging spec
tasks/          YAML task bank (pilot: ~20 seed tasks)
judges/         LLM judge prompt templates
harness/        Python CLI (run → judge → report)
config/         Default weights and run settings
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
