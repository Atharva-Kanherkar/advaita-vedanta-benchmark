"""Fast, resumable, parallel judge finisher. Skips judgments already on disk,
grades the rest 8-at-a-time, then writes consistency + report."""
import json, sys, threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from harness.cli import load_dotenv
from harness.judge import (_judge_consistency, _render_transcript, judge_response,
                           resolve_model_fn)
from harness.report import generate_report, print_report
from harness.schema import Judgment
from harness.tasks import load_task_map

load_dotenv()
RUN = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/20260708T170203Z-2dfb2836")
TASKS = Path("tasks")
JUDGE = "openai:gpt-5.4"
TEMPLATE = "rubric_judge_strict.txt"

task_map = load_task_map(TASKS)
grouped: dict = defaultdict(list)
for line in (RUN / "responses.jsonl").read_text().splitlines():
    if line.strip():
        r = json.loads(line)
        grouped[(r["model"], r["task_id"].split("@")[0])].append(r)

judged_path = RUN / "judged.jsonl"
done = set()
if judged_path.exists():
    for line in judged_path.read_text().splitlines():
        if line.strip():
            j = json.loads(line)
            done.add((j["model"], j["task_id"]))

todo = [(m, b, recs) for (m, b), recs in grouped.items()
        if (m, b) not in done and task_map.get(b)]
print(f"{len(done)} already judged, {len(todo)} remaining", flush=True)

judge_fn = resolve_model_fn(JUDGE)
lock = threading.Lock()
f = judged_path.open("a", encoding="utf-8")
n = [0]


def work(item):
    m, b, recs = item
    task = task_map[b]
    try:
        if len(recs) > 1:
            fin = max(recs, key=lambda r: len(r["messages"]))
            j = judge_response(task, fin["response"], m, JUDGE, judge_fn=judge_fn,
                               prior_turns=_render_transcript(fin["messages"]), template=TEMPLATE)
        else:
            j = judge_response(task, recs[0]["response"], m, JUDGE, judge_fn=judge_fn, template=TEMPLATE)
    except Exception as e:
        print("  skip", m, b, str(e)[:80], flush=True)
        return
    with lock:
        f.write(j.model_dump_json() + "\n")
        f.flush()
        n[0] += 1
        if n[0] % 25 == 0:
            print(f"  judged {n[0]}/{len(todo)}", flush=True)


with ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(work, todo))
f.close()
print(f"rubric judging complete (+{n[0]})", flush=True)

# Consistency (needs all judgments) + report.
all_j = [Judgment(**json.loads(l)) for l in judged_path.read_text().splitlines() if l.strip()]
_judge_consistency(RUN, task_map, all_j, JUDGE, judge_fn)
report = generate_report(RUN, TASKS)
print_report(report)
print("REPORT_DONE", flush=True)
