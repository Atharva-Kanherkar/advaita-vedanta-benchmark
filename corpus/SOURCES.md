# AdvaitaBench Corpus

The corpus serves two jobs, both aimed at the benchmark's biggest validity
threats — **judge circularity** and **training-data contamination**:

1. **Held-out passages** for `text_grounded` tasks, mined from *less-famous*
   sections of the commentarial literature (not the three verses every model
   has seen a thousand times).
2. **Judge reference material** — the relevant source excerpt attached to a
   task so the judge grades against text, not its own parametric prior.

## Primary source: GRETIL

[GRETIL](https://gretil.sub.uni-goettingen.de/gretil.html) (Göttingen Register
of Electronic Texts in Indian Languages) provides machine-readable Sanskrit of
Śaṅkara's Upaniṣad-bhāṣyas and related Advaita texts in plain text / TEI-XML /
HTML. It is free for non-commercial scholarly use with attribution.

Confirmed available (see `sources.yaml`): Aitareya, Taittirīya (explicitly
`-zaMkarabhASya`), Chāndogya, Bṛhadāraṇyaka, Īśa, Māṇḍūkya (+ Gauḍapāda-kārikā),
Praśna Upaniṣad commentaries.

Fetch and hash:

```bash
python -m scripts.fetch_corpus            # verified entries
python -m scripts.fetch_corpus --all      # include to-confirm paths
```

Raw text lands in `corpus/raw/` and hashes in `corpus/manifest.json` (both
gitignored). Task passages cite their source snapshot by SHA-256.

## English reference translations (public domain)

Used to scaffold the `reference_answer` field on tasks. Public-domain so they
can be quoted and redistributed:

- **Bhagavad-Gītā with Śaṅkara's commentary**, tr. A. Mahādeva Śāstrī (1897) —
  [archive.org](https://archive.org/details/Bhagavad-Gita.with.the.Commentary.of.Sri.Shankaracharya)
- **Vedānta-Sūtras with Śaṅkara's commentary**, tr. George Thibaut (SBE 34/38) —
  public domain.

Modern translations (Gambhīrānanda, Mādhavānanda / Advaita Ashrama) are **still
under copyright** — cite, do not redistribute. Reference answers must be written
in our own words, using the Sanskrit (public domain) as ground truth.

## Provenance discipline

Every task carries a `provenance` field, reported stratified:

| Value | Meaning | Contamination risk |
|-------|---------|--------------------|
| `canonical` | Famous verse / stock question, verbatim in training data | High — measures recall |
| `paraphrased` | Same doctrine, reworded, proper nouns stripped | Medium |
| `novel` | Written by us; never published (new riddles, transfer scenarios) | Low — measures understanding |

The **canonical − novel** score gap is itself a headline result: a large gap
means a model is leaning on memorization rather than doctrinal competence.
