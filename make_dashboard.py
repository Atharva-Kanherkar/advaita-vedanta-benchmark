"""Render report.json into a self-contained, aesthetic HTML leaderboard."""
import json, sys
from pathlib import Path

RUN = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/20260708T170203Z-2dfb2836")
report = json.loads((RUN / "report.json").read_text())
models = report["models"]

FAMILIES = [
    ("concept_precision", "Concept"),
    ("level_of_reality", "Levels"),
    ("school_discrimination", "Schools"),
    ("text_grounded", "Text"),
    ("misconception_repair", "Repair"),
    ("consistency_adversarial", "Consistency"),
    ("open_elicitation", "Open"),
    ("sustained_dialectic", "Dialectic"),
]


def short(m):  # pretty model name
    return m.split(":", 1)[-1].split("/")[-1]


def color(v):  # muted red -> gold -> green
    if v is None:
        return "#333"
    if v < 40:
        return "#a3452f"
    if v < 60:
        return "#b9772f"
    if v < 75:
        return "#c99a3e"
    if v < 88:
        return "#b5a54a"
    return "#7f9b52"


ranked = sorted(models.items(), key=lambda kv: kv[1]["composite_score"], reverse=True)
top = ranked[0][1]["composite_score"] if ranked else 100

rows = []
for rank, (m, d) in enumerate(ranked, 1):
    fam = d["family_scores"]
    cells = "".join(
        f'<td class="s" style="background:{color(fam.get(k))}">'
        f'{fam.get(k, 0):.0f}</td>' for k, _ in FAMILIES
    )
    gap = d.get("canonical_minus_novel")
    gap_s = f"{gap:+.0f}" if gap is not None else "—"
    tags = " ".join(f'<span class="tag">{t} · {c}</span>'
                    for t, c in (d.get("top_failure_tags") or [])[:3])
    bar = 100 * d["composite_score"] / top if top else 0
    rows.append(f"""
    <tr>
      <td class="rank">{rank}</td>
      <td class="model">{short(m)}<div class="tags">{tags}</div></td>
      <td class="comp">
        <div class="barwrap"><div class="bar" style="width:{bar:.1f}%"></div></div>
        <span class="cval">{d['composite_score']:.1f}</span>
      </td>
      {cells}
      <td class="gap">{gap_s}</td>
    </tr>""")

head = "".join(f'<th class="fh">{lbl}</th>' for _, lbl in FAMILIES)
html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>AdvaitaBench Leaderboard</title>
<style>
:root{{--bg:#0a0c17;--panel:#11142a;--gold:#d4a24e;--bone:#f2ecdc;--dim:#8b8fa8;}}
*{{box-sizing:border-box}}
body{{margin:0;background:radial-gradient(1200px 600px at 50% -10%,#161a33,#0a0c17);
color:var(--bone);font-family:-apple-system,Segoe UI,Roboto,sans-serif;padding:48px 32px 80px}}
.wrap{{max-width:1100px;margin:0 auto}}
h1{{font-family:Baskerville,Georgia,serif;font-weight:500;font-size:40px;letter-spacing:.5px;
margin:0 0 4px;color:var(--bone)}}
h1 .om{{color:var(--gold)}}
.sub{{color:var(--dim);font-size:14px;margin-bottom:34px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{color:var(--dim);font-weight:500;text-align:center;padding:0 6px 14px;font-size:11px;
text-transform:uppercase;letter-spacing:.8px}}
th.l{{text-align:left}}
td{{padding:12px 6px;border-top:1px solid #1e2240;vertical-align:middle}}
.rank{{color:var(--gold);font-family:Baskerville,Georgia,serif;font-size:20px;width:34px;text-align:center}}
.model{{font-weight:600;font-size:15px;min-width:170px}}
.tags{{margin-top:5px}}
.tag{{display:inline-block;background:#1c2038;color:#a97b6d;border:1px solid #2a2f52;
border-radius:20px;padding:1px 8px;font-size:10px;margin:2px 4px 0 0}}
.comp{{min-width:190px}}
.barwrap{{background:#1a1e38;border-radius:6px;height:9px;overflow:hidden;display:inline-block;
width:120px;vertical-align:middle}}
.bar{{height:100%;background:linear-gradient(90deg,#8a6a2e,var(--gold));border-radius:6px}}
.cval{{font-weight:700;margin-left:10px;color:var(--gold);font-size:16px}}
td.s{{text-align:center;color:#0a0c17;font-weight:700;border-radius:5px;width:52px;
border-top:2px solid #0a0c17}}
.gap{{text-align:center;color:var(--dim);font-weight:600}}
.note{{color:var(--dim);font-size:12px;margin-top:26px;line-height:1.6;max-width:760px}}
</style></head><body><div class="wrap">
<h1>AdvaitaBench <span class="om">·</span> Leaderboard</h1>
<div class="sub">Advaita Vedānta doctrinal competence · {len(models)} models · judged by GPT-5.4 · strict rubric v2 · school-pinned, closed-book</div>
<table>
<thead><tr><th></th><th class="l">Model</th><th class="l">Composite</th>{head}<th class="fh">C−N</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<div class="note">
Composite is the weighted mean across eight families (0–100). Family cells are
colour-graded low→high. <b>C−N</b> is the canonical-minus-novel gap: high = the
model leans on memorised material more than genuine reasoning.
Failure-tag chips show each model's most common doctrinal errors.
Strict rubric: 4/4 reserved for flawless-and-complete; missed required distinctions and affirmed forbidden claims carry hard caps. Judge: GPT-5.4 (reserved, non-subject).
</div>
</div></body></html>"""

out = Path("marketing/dashboard.html")
out.write_text(html, encoding="utf-8")
print("DASHBOARD:", out.resolve())
