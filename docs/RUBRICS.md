# AdvaitaBench Rubrics

Per-family scoring dimensions. Each dimension uses the **0–4 scale** defined in `METHODOLOGY.md`.

Judge output must include: `dimension_scores`, `failure_tags`, `rationale`, and (where applicable) `doctrine_signature`.

---

## Global failure tags

Apply across families when triggered:

| Tag | Description |
|-----|-------------|
| `school_mixing` | Conflates Advaita with another school without explicit comparison |
| `new_age_nonduality` | Generic “all is one” without Advaita technical apparatus |
| `level_collapse` | Flattens paramārthika/vyāvahārika/prātibhāsika |
| `nihilistic_denial` | Claims vyāvahārika is “false” in a dismissive/literal sense |
| `straw_man_user` | Misrepresents the questioner’s concern |
| `text_ungrounded` | Required passage not cited or misquoted |
| `sanskrit_misuse` | Technical term used incorrectly |
| `sycophantic_agreement` | Agrees with a false premise in the user prompt |
| `doctrine_drift` | Contradicts model’s own earlier turn without justification |

---

## 1. Concept precision

| Dimension | Weight | Score 4 requires… |
|-----------|--------|-------------------|
| `term_accuracy` | 0.35 | Correct definitions for all terms in scope |
| `distinction_clarity` | 0.35 | Explicit contrast (not synonym collapse) |
| `advaita_framing` | 0.20 | Positions terms within Advaita ontology |
| `pedagogical_clarity` | 0.10 | Accessible without sacrificing precision |

**Automatic cap:** If `term_accuracy ≤ 1` on any core term in the prompt, max task score = 40.

**Example gold distinctions (non-exhaustive):**
- Brahman ≠ Īśvara (saguṇa/sopādhika vs nirguṇa)
- Ātman ≠ jīva (jīva = ātman + upādhi-s / avidyā-kārya presentation)
- avidyā ≠ māyā (often distinguished: avidyā = individual ignorance; māyā = cosmic principle — note commentarial variation)
- sākṣī ≠ antaḥkaraṇa (witness vs mental apparatus)
- mithyā ≠ tuccha (dependent reality vs absolute non-existence)

---

## 2. Level-of-reality reasoning

| Dimension | Weight | Score 4 requires… |
|-----------|--------|-------------------|
| `level_identification` | 0.30 | Correctly identifies which level(s) the question targets |
| `non_contradiction` | 0.30 | No flat contradictions across levels in one answer |
| `vyavahara_respect` | 0.25 | Honors ethical/practical validity at vyāvahārika |
| `paramartha_precision` | 0.15 | Paramārthika claims qualified correctly |

**Automatic cap:** `level_collapse` or `nihilistic_denial` → max task score = 25.

**Score 4 exemplar pattern:**
> “At paramārthika, only Brahman; at vyāvahārika, karma-phala and dharma operate for the jīva under avidyā. The levels are not competing facts.”

---

## 3. School discrimination

| Dimension | Weight | Score 4 requires… |
|-----------|--------|-------------------|
| `advaita_position` | 0.35 | Correct classical Advaita claim |
| `contrast_accuracy` | 0.35 | Fair, accurate contrast with the named school |
| `no_ecumenism` | 0.20 | Avoids “all schools agree” unless precisely qualified |
| `attribution_hygiene` | 0.10 | Does not attribute foreign views to Śaṅkara |

**Automatic cap:** `school_mixing` on primary contrast → max task score = 30.

---

## 4. Text-grounded interpretation

| Dimension | Weight | Score 4 requires… |
|-----------|--------|-------------------|
| `claim_extraction` | 0.25 | Identifies the passage’s central claim |
| `textual_evidence` | 0.35 | Cites specific words/phrases from the supplied passage |
| `interpretive_restraint` | 0.25 | No over-reading beyond the passage + standard Advaita hermeneutic |
| `concept_mapping` | 0.15 | Maps claim to correct Advaita concept |

**Automatic cap:** `text_ungrounded` → max task score = 20.

**Required output structure (subject model):**
1. Claim (1–2 sentences)
2. Evidence (quoted span)
3. Advaita concept
4. Optional: what the passage does *not* claim

---

## 5. Misconception repair

Scored **per conversation** (all turns jointly).

| Dimension | Weight | Score 4 requires… |
|-----------|--------|-------------------|
| `misconception_identified` | 0.25 | Names the confusion precisely |
| `correction_quality` | 0.35 | Advaita-correct repair with distinctions |
| `dialogue_stability` | 0.25 | Does not flip doctrine under user pushback |
| `pedagogical_tone` | 0.15 | Firm correction without condescension or capitulation |

**Turn-level flags:** Apply `sycophantic_agreement` if any turn accepts the misconception.

**Canonical repair anchors:**

| Misconception | Required repair elements |
|---------------|-------------------------|
| Morality under Brahman | vyāvahārika validity; avidyā; jīva’s kartṛtva until jñāna |
| World doesn’t exist | mithyā / adhyāsa; not tuccham; empirical order within avidyā |
| Who attains? | jīva is provisional; jñāna is of Ātman/Brahman identity; mokṣa is not an event for a real agent at paramārthika |

---

## 6. Consistency and adversarial robustness

Scored at **variant group** level.

| Dimension | Weight | Score 4 requires… |
|-----------|--------|-------------------|
| `doctrine_consistency` | 0.45 | Same core doctrine across all variants |
| `robustness_to_framing` | 0.25 | Hostile/emotional framing doesn’t change answer |
| `terminology_invariance` | 0.20 | Sanskrit vs English versions align |
| `adversarial_integrity` | 0.10 | Resists false authority (“ChatGPT said…”) |

**Group score formula:**
```
group_score = doctrine_consistency × 0.6 + mean(individual_variant_scores) × 0.4
```

**Automatic cap:** Any variant with `school_mixing` → group max = 35.

---

## 7. Open elicitation

Vague, term-free existential prompts ("who am I?", "why does none of this feel
real?"). The user turn contains **no** technical vocabulary and does **not**
ask for Vedānta — the school is pinned only by the system prompt. Tests whether
the model reaches for genuine Advaita apparatus or dissolves into generic
spirituality.

| Dimension | Weight | Score 4 requires… |
|-----------|--------|-------------------|
| `apparatus_presence` | 0.35 | Brings the correct Advaita apparatus the question calls for (e.g. for "what am I?": ātman ≠ body/mind/ego, sākṣī, dṛg-dṛśya-viveka; for suffering: adhyāsa, avidyā) |
| `doctrinal_correctness` | 0.30 | What it asserts is Advaita-correct and level-aware |
| `resists_vagueness` | 0.25 | Does **not** collapse into "you are the universe / all is love / manifest your reality" New Age mush |
| `pedagogical_grounding` | 0.10 | Meets the sincere questioner accessibly without sacrificing precision |

**Automatic cap:** `new_age_nonduality` → max task score = 35 (global tag).

**Primary failure modes:** New Age substitution, secular-existentialist answer with no Advaita content, level collapse, "sounds wise" with zero technical apparatus.

**Note:** Run under `school_pinned` (leaderboard default) and, as a contrast, `neutral` — the neutral condition additionally tests whether the model even reaches for Advaita unprompted.

---

## 8. Sustained dialectic

Śruti-pressure dialogues (vāda genre). The model states a doctrinal position;
each scripted pushback cites a **genuine** canonical text that apparently
contradicts it, escalating to a script cap (3–4 pushbacks). Tests whether the
model can reconcile the citation the way the tradition actually does
(adhyāropa-apavāda, adhikāri-bheda, level distinction, tātparya-liṅgas)
without capitulating, dismissing śruti, or inventing hermeneutics.

Scored **per conversation** on the full transcript.

| Dimension | Weight | Score 4 requires… |
|-----------|--------|-------------------|
| `doctrine_stability` | 0.35 | Position held through every pushback; no drift, no capitulation |
| `sruti_reconciliation` | 0.35 | The cited text is engaged and reconciled by the tradition's actual hermeneutic — not waved away, not conceded |
| `argument_quality` | 0.20 | Arguments given, not asserted; counter-texts or criteria deployed where the tradition has them |
| `tone_under_pressure` | 0.10 | Firm without contempt; treats the opponent's citation as genuine śruti |

**Automatic caps:** `sycophantic_agreement` → max 30; `level_collapse` / `nihilistic_denial` → max 25.

**Primary failure modes:** capitulation at turn N after a correct turn 1, dismissing the cited verse as unimportant/interpolated, fake hermeneutics (invented rules), sliding into another school's reconciliation (e.g. conceding bhedābheda), "both are true somehow" mush.

---

## Aggregate reporting

Report per model:

- Overall AdvaitaBench score
- Per-family scores (6 bars)
- Top 5 failure tags
- Consistency score (family 6 only)
- Stratification: `language`, `source_tier`, `system_prompt_condition`
