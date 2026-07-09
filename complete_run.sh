#!/bin/bash
# Complete the AdvaitaBench run without re-calling the 3 already-finished
# Anthropic models. Runs the remaining 11 subject models into a fresh dir,
# splices in Fable 5 / Opus 4.8 / Sonnet 5 from the stopped run, then judges
# and reports the combined 14-model set.
set -uo pipefail
cd ~/Projects/advaita-vedanta-benchmark
source .venv/bin/activate

OLD="runs/20260708T113300Z-f46a9966"
echo "START $(date)"

# gpt-5.5 was only 106/123 when the run stopped, so redo it fully; the other
# 10 were never started. The 3 Anthropic flagships are complete and reused.
advaita-bench run --models "openai:gpt-5.5,openai:gpt-5.2,google:gemini-3.1-pro-preview,x-ai/grok-4.3,deepseek/deepseek-v4-pro,qwen/qwen3.7-max,z-ai/glm-5.2,moonshotai/kimi-k2.6,minimax/minimax-m3,mistralai/mistral-medium-3-5,tencent/hy3"
if [ $? -ne 0 ]; then echo "RUN_FAILED $(date)"; exit 1; fi

NEW=$(ls -td runs/*/ | head -1)
echo "NEW=$NEW"

# Splice the already-complete Claude models into the new run's responses.
python3 - "$OLD/responses.jsonl" "$NEW/responses.jsonl" <<'PY'
import json, sys
old, new = sys.argv[1], sys.argv[2]
keep = {"anthropic:claude-fable-5", "anthropic:claude-opus-4-8", "anthropic:claude-sonnet-5"}
n = 0
with open(new, "a") as out:
    for line in open(old):
        if not line.strip():
            continue
        if json.loads(line)["model"] in keep:
            out.write(line if line.endswith("\n") else line + "\n")
            n += 1
print(f"spliced {n} Claude records into {new}")
PY

advaita-bench judge --run "$NEW"  && advaita-bench report --run "$NEW"
echo "ALL_DONE $(date) NEW=$NEW"
