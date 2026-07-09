# AdvaitaBench Launch Thread

Copy-paste ready. No emojis. Attach the PNGs from `docs/tweet-assets/` where noted.

---

**Tweet 1/8**  
Introducing AdvaitaBench — a closed-book eval of whether frontier models can hold precise Advaita distinctions under pressure, or only sound wise.

84 tasks. 10 models. Two independent judges. Bias-corrected headline score.

Thread below.

**Attach:** `01-hero-viewport.png`

---

**Tweet 2/8**  
LLMs are fluent on "non-duality." They are weaker at keeping Advaita distinct from Dvaita, Buddhism, Sāṃkhya, or New Age mush — and at keeping doctrine stable when the user pushes.

That is the failure mode this benchmark is built to measure.

---

**Tweet 3/8**  
What we test (8 families):

- Concept precision
- Level-of-reality reasoning
- School discrimination
- Text-grounded interpretation
- Misconception repair (multi-turn)
- Consistency under rephrasing
- Open elicitation ("Who am I?")
- Sustained dialectic (scripture quoted against the model)

**Attach:** `06-tasks.png`

---

**Tweet 4/8**  
What we measure (8 families):

- Concept precision
- Level-of-reality reasoning
- School discrimination
- Text-grounded interpretation
- Misconception repair (multi-turn)
- Consistency under rephrasing
- Open elicitation ("Who am I?")
- Sustained dialectic (scripture quoted against the model)

---

**Tweet 5/8**  
Design for labs, not vibes:

- Closed-book (no web, no RAG)
- Reference answers + forbidden claims
- Hard score caps for known failure modes (school mixing, level collapse, nihilism, New Age mush)
- Novel tasks written for this benchmark so memorization does not win

---

**Tweet 6/8**  
Judge bias is real, so we measured it.

Two judges (lenient Anthropic + strict OpenAI). Each favored its own maker's models. We subtracted that bias into AdvaitaBench-N (field average = 50).

If your eval stack only uses one judge family, your ranking may be an artifact.

**Attach:** `03-judge-slope.png`

---

**Tweet 7/8**  
Pilot leaderboard (July 2026, AdvaitaBench-N):

1. claude-fable-5 — 62.7
2. claude-opus-4-8 — 59.9
3. gpt-5.5 — 58.0
4. gpt-5.2 — 56.2
5. qwen3.7-max — 48.8
6. deepseek-v4-pro — 48.0
7. glm-5.2 — 46.6
8. gemini-3.1-pro-preview — 46.4
9. grok-4.3 — 43.5
10. claude-sonnet-5 — 16.8 (14 blank responses)

Top of the field is tight. Verbosity does not buy understanding.

**Attach:** `02-leaderboard-frontier.png`  
**Optional 2nd:** `04-skill-fingerprint.png`

---

**Tweet 8/8**  
Site: https://docs-alpha-smoky.vercel.app  
Blog / methodology: https://docs-alpha-smoky.vercel.app/blog.html  
Code + tasks: https://github.com/Atharva-Kanherkar/advaita-vedanta-benchmark

Pilot caveats: single sample per task, two-judge ensemble, no human adjudication yet. Ranks 1–4 sit within judge disagreement. Measures doctrinal competence only.

**Attach:** `05-leaderboard-section.png`

---

## Attachment map

| Tweet | File |
|-------|------|
| 1 | `01-hero-viewport.png` |
| 3 | `06-tasks.png` |
| 6 | `03-judge-slope.png` |
| 7 | `02-leaderboard-frontier.png` (+ optional `04-skill-fingerprint.png`) |
| 8 | `05-leaderboard-section.png` |

Path: `/Users/atharva/Projects/advaita-vedanta-benchmark/docs/tweet-assets/`
