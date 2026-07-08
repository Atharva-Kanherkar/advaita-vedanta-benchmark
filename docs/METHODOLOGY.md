# AdvaitaBench Methodology

**AdvaitaBench** is a research-grade benchmark for evaluating large language models on **classical Advaita Vedānta** — not generic “non-duality,” not pan-Indian philosophy, and not undifferentiated Vedānta ecumenism.

Version: **0.1.0-draft**  
Reference tradition: **Classical Advaita** (Śaṅkara, Sureśvara, Padmapāda, Vivekacūḍāmaṇi in Advaita commentarial lineage)  
Status: **Pilot harness + seed tasks** (publication requires expanded task bank and human adjudication)

---

## 1. Research question

> How reliably can current LLMs **teach, interpret, and defend Advaita Vedānta** without conflating schools, collapsing levels of reality, or reproducing popular misconceptions?

This is distinct from:

- **General religious QA** (factual trivia about Hinduism)
- **Sanskrit translation** (lexical competence without doctrinal precision)
- **“Spiritual chatbot” quality** (tone, empathy, vagueness)

AdvaitaBench measures **doctrinal competence under pressure**.

---

## 2. Design principles

| Principle | Operational meaning |
|-----------|---------------------|
| **School-pinned** | Every task declares a target school (`advaita` by default). Mixing Dvaita/Viśiṣṭādvaita/Buddhist/Yoga/Sāṃkhya answers without explicit comparison is a **failure mode**, not a stylistic choice. |
| **Level-aware** | Correct answers must respect **paramārthika / vyāvahārika / prātibhāsika** distinctions and avoid flat contradictions. |
| **Text-grounded when required** | Interpretation tasks supply a passage; models must cite the passage, not free-associate from training prior. |
| **Misconception-aware** | Many user prompts encode **known confusions** (morality under Brahman, “world doesn’t exist,” “who attains?”). Repair requires **correction without straw-manning**. |
| **Robust under rephrasing** | Consistency tasks present the **same doctrinal problem** with varied wording, emotion, and terminology. Doctrine should not flip. |
| **Auditable grading** | Every score decomposes into rubric dimensions with judge rationale and failure tags. |

---

## 3. Task families

Six families form the benchmark. Each family tests a different failure surface.

### 3.1 Concept precision (`concept_precision`)

**Goal:** Distinguish closely related technical terms.

Core lexicon (non-exhaustive): Brahman, Ātman, jīva, Īśvara, māyā, avidyā, sākṣī, upādhi, mithyā, adhyāsa, vṛtti, antaḥkaraṇa.

**Task types:**
- Definition discrimination (“How is jīva different from Ātman in Advaita?”)
- Contrast pairs (“Is avidyā identical to māyā?”)
- Boundary tests (“Can sākṣī be called a ‘faculty’?”)

**Primary failure modes:** synonym collapse, Dvaita imports, “everything is one word” vagueness.

### 3.2 Level-of-reality reasoning (`level_of_reality`)

**Goal:** Apply **paramārthika**, **vyāvahārika**, and **prātibhāsika** perspectives without contradiction.

**Task types:**
- Two-level explanations (why ethics matters if Brahman alone is real)
- Error diagnosis (“This answer confuses vyāvahārika denial with paramārthika truth”)
- Scenario reasoning (dream, snake-rope, post-liberation conduct)

**Primary failure modes:** literal world-denial, paramārthika/vyāvahārika collapse, pratibhāsika treated as “unimportant.”

### 3.3 School discrimination (`school_discrimination`)

**Goal:** Prevent illegitimate school-mixing.

**Contrasts tested:** Advaita vs Dvaita, Viśiṣṭādvaita, Buddhism (anātman/śūnyatā), Sāṃkhya (puruṣa-prakṛti), Yoga (puruṣa), generic New Age non-duality.

**Task types:**
- “What would Advaita say vs Dvaita?”
- Trap questions that invite ecumenical mush
- Identify-the-school given a position statement

**Primary failure modes:** “All paths say the same,” attributing Viśiṣṭādvaita’s qualified non-duality to Śaṅkara, Buddhist śūnyatā = Brahman without argument.

### 3.4 Text-grounded interpretation (`text_grounded`)

**Goal:** Given a passage from canonical or commentarial sources, extract the **claim** and justify it **from the text**.

**Source tiers:**
- **Tier A:** Upaniṣads, Bhagavad Gītā (Śaṅkara bhāṣya where relevant)
- **Tier B:** Brahma Sūtra / commentarial excerpts, Vivekacūḍāmaṇi
- **Tier C:** Modern Advaita teachers (explicitly labeled; lower weight in aggregate until bank expands)

**Task types:**
- “What is the author asserting in this verse?”
- “Which Advaita concept is being applied here?”
- “What would be an over-reading of this passage?”

**Primary failure modes:** eisegesis, ignoring key terms in the passage, importing non-Advaita frameworks.

### 3.5 Misconception repair (`misconception_repair`)

**Goal:** Multi-turn correction of **common distortions**.

Canonical misconception threads (seed set):
1. “If everything is Brahman, why can’t I ignore morality?”
2. “Does Advaita say the physical world literally does not exist?”
3. “If there is no individual self, who attains liberation?”

**Task types:** 2–4 turn dialogues where the user pushes back.

**Primary failure modes:** agreeing with the misconception, over-correction into nihilism, abandoning Advaita for Dvaita mid-conversation.

### 3.6 Consistency and adversarial robustness (`consistency_adversarial`)

**Goal:** Same doctrine, different surface form — answers must **cohere**.

**Perturbation axes:**
- Wording (Sanskrit terms vs plain English)
- Emotional framing (curious vs hostile vs anxious)
- Authority challenge (“ChatGPT said Advaita is X”)
- Scope shift (personal vs metaphysical)

**Task types:** **Variant groups** — 3–5 prompts sharing a `variant_group_id` and `gold_doctrine_key`.

**Primary failure modes:** doctrine drift across variants, sycophantic agreement with false premises, unnecessary contradiction between turns.

### 3.7 Open elicitation (`open_elicitation`)

**Goal:** Measure **unprompted doctrinal fidelity**. The user asks a vague,
term-free existential question ("who am I?", "why do I feel something is
missing?") that names no technical vocabulary and does not request Vedānta. The
school is pinned only by the system prompt.

**Task types:**
- Stock existential questions (canonical provenance)
- Oblique, emotionally framed versions (paraphrased)
- Transfer scenarios that force applying the apparatus fresh — dementia and the
  persisting self, atom-for-atom duplication, flow-state absorption (novel)

**Primary failure modes:** New Age substitution ("you are the universe"),
secular-existentialist answer with no Advaita apparatus, level collapse, "sounds
wise" with no technical content.

---

## 4. Scoring architecture

### 4.1 Rubric scale (per dimension)

| Score | Label | Meaning |
|-------|-------|---------|
| 0 | **Wrong / harmful** | Doctrinally incorrect, school-mixed, or reinforces misconception |
| 1 | **Serious error** | Partially relevant but core claim is wrong or unstable |
| 2 | **Weak** | Directionally right; missing distinctions, hedging, or incomplete repair |
| 3 | **Competent** | Advaita-correct with minor imprecision |
| 4 | **Excellent** | Precise, level-aware, well-structured; cites text when required |

Dimensions are **family-specific** (see `RUBRICS.md`). Task score = weighted mean of dimensions, scaled to **0–100**.

### 4.2 Composite benchmark score

```
family_score_f = mean(task_scores in family f)
AdvaitaBench = Σ (w_f × family_score_f)   where Σ w_f = 1
```

Default weights (pilot):

| Family | Weight | Rationale |
|--------|--------|-----------|
| concept_precision | 0.15 | Foundational vocabulary |
| level_of_reality | 0.18 | Core Advaita distinctive |
| school_discrimination | 0.18 | Most common LLM failure |
| text_grounded | 0.18 | Scholarly grounding |
| misconception_repair | 0.13 | Pedagogical utility |
| consistency_adversarial | 0.08 | Robustness (measured on variant groups) |
| open_elicitation | 0.10 | Unprompted doctrinal fidelity on vague questions |

Weights are configurable in `config/default.yaml`.

### 4.3 Consistency metric (family 6 only)

Family 6 is scored at the **variant-group** level, not per task. A dedicated
consistency judge compares the `doctrine_signature` of every variant in a group
and assigns a max pairwise **distance** (0 equivalent … 3 direct contradiction).
The harness then computes a single group score (implemented in
`harness/judge.py`, one formula — the earlier draft listed three; this is
canonical):

```
consistency_score = 100 × (1 − max_distance / 3)
group_score       = 0.6 × consistency_score + 0.4 × mean(variant final_scores)
```

Distance is rubric-based (signature comparison), not embedding-only. Group
scores are written to `consistency.jsonl` and feed the family-6 family score.

---

## 5. Judging protocol

See `JUDGING.md` for full specification. Summary:

1. **Structured LLM judge** (primary at scale) — separate model from subject, temperature 0, JSON output. The harness **hard-fails** if the judge model also appears as a subject model (override only with `--allow-self-judge`, which marks the run non-publication-grade).
2. **Reference-assisted grading** — tasks carry a full prose `reference_answer` (verify against it, don't generate from prior) plus `gold_points`, `forbidden_claims`, `required_distinctions`. The judge is told to grade against the reference, not its own knowledge — the main mitigation for judge circularity.
3. **Human adjudication subset** — minimum 10% of pilot tasks, target κ ≥ 0.65 inter-annotator agreement before publication
4. **Blinding** — judges never see model identity during scoring
5. **Failure tagging** — every sub-3 score requires ≥1 machine-readable failure tag
6. **Score computed by harness, not judge** — the judge emits only dimension scores + tags; the harness applies weights and caps deterministically.

Judge model must differ from subject model in publication runs (enforced).

---

## 6. Harness workflow

```
tasks/*.yaml  →  run (subject models)  →  responses.jsonl
                                           ↓
                                    judge (rubric JSON)
                                           ↓
                                    report (scores + tags)
```

Commands:

```bash
advaita-bench run --models @frontier,@openrouter    # or explicit specs / @all
advaita-bench judge --run runs/<id>                 # rubric + consistency judges
advaita-bench report --run runs/<id>
```

Each run records model IDs, per-model provider routing, temperature, system
prompt variant, closed-book flag, task count, token usage, and (for OpenRouter
models) actual dollar cost, in `manifest.json`.

### 6.1 Provider routing and cost

Model specs route by provider (`harness/providers.py`), which is also a billing
decision: **OpenAI, Anthropic, and Google** specs hit their native APIs and draw
on first-party credits; **everything else** (xAI/Grok, DeepSeek, Qwen, GLM, Kimi,
Llama, Mistral, …) routes through **OpenRouter** — real out-of-pocket spend,
reported per run. A `provider:` prefix forces a route. Models are declared in
`config/models.yaml` and expanded via `@group` / `@all`.

---

## 7. System prompt policy

Three conditions (report all in publication):

| Condition | Description |
|-----------|-------------|
| **neutral** | “Answer accurately about Advaita Vedānta.” |
| **school_pinned** | “Answer from classical Advaita (Śaṅkara tradition). Do not conflate schools.” |
| **teacher** | “Explain as an Advaita teacher would to a sincere student.” |

Default for leaderboard: **school_pinned**.

**Closed-book.** All conditions are closed-book: subject models receive no
tools, retrieval, or web access. The harness passes no tools and records
`closed_book: true` in the manifest. An open-book track (model + retrieval over
the `corpus/`) is a possible future condition but must be reported separately,
never mixed into a closed-book leaderboard.

---

## 8. Validity threats and mitigations

| Threat | Mitigation |
|--------|------------|
| Judge bias / leniency | Enforced judge≠subject; grade against `reference_answer` not judge prior; human spot-check; report judge-model sensitivity |
| Training-data contamination | `provenance` field (`canonical`/`paraphrased`/`novel`) reported stratified; held-out corpus passages from less-famous sections; the **canonical−novel score gap** is a headline result |
| Sanskrit vs English asymmetry | Tag language; report stratified scores |
| “Sounds wise” without doctrine | Rubric requires explicit distinctions, not tone |
| Ecumenical politeness | `school_discrimination` and `forbidden_claims` penalties |
| Multi-turn sycophancy | `misconception_repair` pushback turns |

---

## 9. Publication checklist

Before calling results “research-grade”:

- [ ] ≥30 tasks per family (pilot: 3–5 each)
- [ ] Human adjudication on ≥10% with reported κ
- [ ] ≥3 subject models + ≥1 distinct judge model
- [ ] Full reproducibility bundle (config, prompts, task hashes, run logs)
- [ ] Failure analysis appendix (top 10 failure tags per model)
- [ ] Explicit scope statement (what AdvaitaBench does **not** measure)

---

## 10. Ethics and scope

- AdvaitaBench evaluates **philosophical accuracy**, not spiritual attainment or guru authenticity.
- Modern teachers appear only when labeled; no benchmark claim about living teachers’ orthodoxy.
- Tasks avoid caste, political, or communal framing unless explicitly testing historical commentarial context.
- Results should not be marketed as “which AI is enlightened.”

---

## References (methodological anchors)

- Śaṅkara, *Brahma Sūtra Bhāṣya* and principal Upaniṣad bhāṣyas
- Sureśvara, *Naiṣkarmya Siddhi* / *Vārtika*
- Swami Madhavananda (trans.), *Vivekacūḍāmaṇi*
- Potter (ed.), *Encyclopedia of Indian Philosophies*, Vol. III (Advaita)
- Nakamura, *A History of Early Vedānta Philosophy*
- Evaluation precedents: MMLU discipline splits, MT-Bench multi-turn, Promptfoo rubric grading, HELM capability-specific evals
