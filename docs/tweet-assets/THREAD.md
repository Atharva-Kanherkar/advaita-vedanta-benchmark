# AdvaitaBench Launch Thread

Copy-paste ready. No emojis. Attach the PNGs from `docs/tweet-assets/` where noted.

---

**Tweet 1/8**  
Introducing AdvaitaBench — a closed-book pressure test for whether frontier models can hold precise philosophical distinctions under attack, or only sound wise.

84 tasks. 10 models. Two independent judges. Bias-corrected headline score.

Thread below.

**Attach:** `01-hero-viewport.png`

---

**Tweet 2/8**  
Why model makers should care:

Your users do not only ask for code and math. They ask for careful reasoning in domains where sounding right is cheap and being right is hard.

If a model melts Advaita into New Age mush the moment you push, that is not a niche religion bug. It is a reliability failure: confident vagueness, school-mixing, and doctrine that flips under pressure.

---

**Tweet 3/8**  
The product question for labs is simple:

Can your model keep a precise position stable when the user argues back — with scripture, hostility, grief, or a rival school?

Trivia leaderboards do not answer that. AdvaitaBench does, because classical Advaita is a web of exact distinctions. Get one wrong and a trained reader notices immediately.

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
Use it if you ship models that reason with people:

Site: https://docs-alpha-smoky.vercel.app  
Blog / methodology: https://docs-alpha-smoky.vercel.app/blog.html  
Code + tasks: https://github.com/Atharva-Kanherkar/advaita-vedanta-benchmark

Pilot caveats: single sample per task, two-judge ensemble, no human adjudication yet. Ranks 1–4 sit within judge disagreement. This measures doctrinal competence — not spiritual attainment.

If you run evals at a lab: what failure mode should we add next?

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
