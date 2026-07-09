# AdvaitaBench

**A research benchmark for Advaita Vedānta doctrinal competence in large language models.**

[**Leaderboard & site**](https://atharva-kanherkar.github.io/advaita-vedanta-benchmark/) ·
[Methodology](docs/METHODOLOGY.md) ·
[Rubrics](docs/RUBRICS.md) ·
[Judging protocol](docs/JUDGING.md)

AdvaitaBench measures whether a model can **teach, interpret, and defend classical Advaita
Vedānta** (Śaṅkara tradition) — without conflating schools, collapsing levels of reality,
reproducing popular misconceptions, or capitulating under pressure. It is not a Hinduism
trivia quiz and not a "spiritual vibes" eval: every task is graded against reference
answers, required distinctions, and forbidden claims, with automatic score caps for
doctrinal failure modes.

## Results (pilot, July 2026)

10 frontier models · 84 tasks · closed-book · temperature 0 · school-pinned prompt.
**AdvaitaBench-N** is a two-judge ensemble score (strict GPT-5.4 + Haiku 4.5) with a
measured self-preference correction — see [normalization](docs/METHODOLOGY.md#51-judge-ensemble-and-score-normalization-advaitabench-n).

| # | Model | AdvaitaBench-N | Strict | Lenient |
|---|-------|---------------:|-------:|--------:|
| 1 | Claude Fable 5 | **62.7** | 73.5 | 99.4 |
| 2 | Claude Opus 4.8 | 59.9 | 71.5 | 99.7 |
| 3 | GPT-5.5 | 58.0 | 75.3 | 98.8 |
| 4 | GPT-5.2 | 56.2 | 73.8 | 99.2 |
| 5 | Qwen 3.7 Max | 48.8 | 66.9 | 98.9 |
| 6 | DeepSeek V4 Pro | 48.0 | 67.7 | 98.1 |
| 7 | GLM 5.2 | 46.6 | 66.3 | 98.6 |
| 8 | Gemini 3.1 Pro | 46.4 | 66.0 | 98.7 |
| 9 | Grok 4.3 | 43.5 | 69.6 | 95.2 |
| 10 | Claude Sonnet 5 | 16.8 | 62.5 | 90.6 |

Headline findings:

- **Judges are family-biased.** Each single judge ranked its own lab's models on top
  (Kendall τ between the two judge rankings: 0.29). The published score standardizes both
  judges and subtracts a difference-in-differences self-preference estimate. The top-4 gap
  is within judge disagreement — treat ranks 1–4 as a cluster.
- **Sustained dialectic is the differentiator.** Multi-turn śruti pressure (genuine
  contradicting citations, escalating for 3–4 scripted turns) spreads models 35–71 where
  single-turn families cluster.
- **No memorization win.** The canonical−novel provenance gap is ≈ 0 under strict grading:
  models succeed (and fail) on reasoning, not recall.
- Sonnet 5's score reflects 14/123 blank responses, carried as failures by design.

*Pilot caveats: single sample per task, two-judge ensemble, no human adjudication yet.
Publication-grade claims require the expanded bank (≥ 30 tasks/family), κ ≥ 0.65 human
agreement, and a third family-neutral judge.*

## Eight task families

| Family | Tests | Weight |
|--------|-------|-------:|
| Concept precision | Brahman ≠ Īśvara ≠ Ātman ≠ jīva; māyā/avidyā/mithyā; bādha vs abhāva | 0.13 |
| Levels of reality | paramārthika / vyāvahārika / prātibhāsika without contradiction | 0.16 |
| School discrimination | vs Dvaita, Viśiṣṭādvaita, Madhyamaka, Sāṃkhya, Kashmir Shaivism, Neo-Vedānta, New Age | 0.16 |
| Text-grounded | Claims justified from supplied passages, incl. held-out bhāṣya excerpts and a distractor text | 0.16 |
| Misconception repair | Multi-turn correction under scripted pushback | 0.12 |
| Consistency | Same doctrine across hostile / Sanskrit / academic / grief framings | 0.07 |
| Open elicitation | "Who am I?" with zero technical vocabulary — apparatus vs mush | 0.09 |
| Sustained dialectic | Yakṣa-praśna-style śruti pressure until a script cap | 0.11 |

Contamination control: every task is tagged `canonical` / `paraphrased` / `novel`, scores
reported stratified. Held-out passages are mined from less-quoted bhāṣya sections
([GRETIL](https://gretil.sub.uni-goettingen.de/) e-texts; see [corpus/SOURCES.md](corpus/SOURCES.md)).

## Quick start

Requires Python ≥ 3.11.

```bash
git clone https://github.com/Atharva-Kanherkar/advaita-vedanta-benchmark
cd advaita-vedanta-benchmark
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # add your API keys

advaita-bench validate          # validate the task bank
python -m pytest tests/ -q      # offline tests, no keys needed

advaita-bench run --models @frontier,@openrouter   # subject responses
advaita-bench judge --run runs/<run_id>            # rubric + consistency judges
advaita-bench report --run runs/<run_id>           # scores, tags, stratification
python scripts/normalize_scores.py                 # two-judge AdvaitaBench-N
```

### Provider routing

Model specs route by provider — which is also a billing decision:

| Spec | Route | Key |
|------|-------|-----|
| `anthropic:claude-*` | Anthropic API | `ANTHROPIC_API_KEY` |
| `openai:gpt-*` | OpenAI API | `OPENAI_API_KEY` |
| `google:gemini-*` | Gemini API | `GEMINI_API_KEY` |
| everything else (Grok, DeepSeek, Qwen, GLM, Kimi, …) | OpenRouter | `OPENROUTER_API_KEY` |

Model sets live in [`config/models.yaml`](config/models.yaml) (`@frontier`, `@openrouter`,
`@smoke`, `@all`). Each run records routing, token usage, and OpenRouter dollar cost in its
manifest. The harness **enforces judge ≠ subject**.

## Repository layout

```
docs/          Methodology, rubrics, judging spec + the static site (GitHub Pages)
tasks/         YAML task bank (84 tasks, 8 families)
judges/        Judge prompt templates (v1 + strict v2)
harness/       Python package: providers → runner → judge → report
scripts/       Task validation, corpus fetch, score normalization
config/        Family weights, model registry
corpus/        Source-text manifest + fetch/hash script
results/       Published normalized results
tests/         Offline test suite (no API keys)
```

## Scope and ethics

**In scope:** classical Advaita (Śaṅkara tradition), doctrinal precision, pedagogy under
pressure. **Out of scope:** spiritual attainment, guru authentication, caste/politics,
non-Advaita schools except as explicit contrast. Results must not be marketed as "which AI
is enlightened."

## License

MIT.
