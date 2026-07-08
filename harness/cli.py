from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from harness.judge import SelfJudgeError, judge_run
from harness.registry import default_judge, expand_models, load_registry
from harness.report import generate_report, print_report
from harness.runner import run_benchmark

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASKS = ROOT / "tasks"
DEFAULT_RUNS = ROOT / "runs"


def load_dotenv(path: Path | None = None) -> None:
    """Load KEY=VALUE lines from .env at repo root into os.environ.

    Real environment variables win over the file. Lines starting with '#'
    and blank lines are ignored; surrounding quotes on values are stripped.
    """
    path = path or ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key:
            os.environ.setdefault(key, value)


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="AdvaitaBench — Advaita Vedānta LLM benchmark")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run subject models on tasks")
    run_p.add_argument("--models", required=True,
                       help="Comma list of specs or @groups (e.g. @frontier,@openrouter,@all)")
    run_p.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    run_p.add_argument("--output", type=Path, default=DEFAULT_RUNS)
    run_p.add_argument("--system", default="school_pinned",
                       choices=["neutral", "school_pinned", "teacher"])
    run_p.add_argument("--family", default=None, help="Limit to one task family")
    run_p.add_argument("--limit", type=int, default=None, help="Cap number of tasks (smoke runs)")
    run_p.add_argument("--dry-run", action="store_true")

    judge_p = sub.add_parser("judge", help="Grade responses with rubric + consistency judges")
    judge_p.add_argument("--run", type=Path, required=True, help="Run directory")
    judge_p.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    judge_p.add_argument("--judge-model", default=None,
                         help="Defaults to registry `judge`. Must differ from subject models.")
    judge_p.add_argument("--allow-self-judge", action="store_true",
                         help="Bypass judge≠subject guard (not publication-grade)")
    judge_p.add_argument("--dry-run", action="store_true")

    report_p = sub.add_parser("report", help="Aggregate judged scores")
    report_p.add_argument("--run", type=Path, required=True)
    report_p.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)

    validate_p = sub.add_parser("validate", help="Validate task YAML files")
    validate_p.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)

    models_p = sub.add_parser("models", help="Show the model registry and how a spec expands")
    models_p.add_argument("--expand", default=None, help="Preview expansion of a --models value")

    args = parser.parse_args()

    if args.command == "run":
        models = expand_models(args.models)
        if not models:
            raise SystemExit("No models resolved from --models")
        run_path = run_benchmark(
            tasks_dir=args.tasks, models=models, output_dir=args.output,
            system_condition=args.system, family=args.family,
            dry_run=args.dry_run, limit=args.limit,
        )
        _print_run_summary(run_path)
        print(f"Run complete: {run_path}")

    elif args.command == "judge":
        judge_model = args.judge_model or default_judge()
        if not judge_model:
            raise SystemExit("No judge model: pass --judge-model or set `judge` in config/models.yaml")
        try:
            judged = judge_run(args.run, args.tasks, judge_model,
                               dry_run=args.dry_run, allow_self_judge=args.allow_self_judge)
        except SelfJudgeError as exc:
            raise SystemExit(f"ERROR: {exc}")
        print(f"Judging complete: {judged}")

    elif args.command == "report":
        report = generate_report(args.run, args.tasks)
        print_report(report)
        print(f"Report written: {args.run / 'report.json'}")

    elif args.command == "validate":
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from scripts.validate_tasks import validate

        errors = validate(args.tasks)
        if errors:
            for e in errors:
                print(f"ERROR: {e}")
            raise SystemExit(1)
        print(f"All tasks valid under {args.tasks}")

    elif args.command == "models":
        reg = load_registry()
        if args.expand:
            for m in expand_models(args.expand, reg):
                print(m)
        else:
            print(f"judge: {reg.get('judge')}")
            for name, members in (reg.get("groups") or {}).items():
                print(f"\n@{name} ({len(members)}):")
                for m in members:
                    print(f"  {m}")


def _print_run_summary(run_path: Path) -> None:
    manifest = json.loads((run_path / "manifest.json").read_text(encoding="utf-8"))
    cost = manifest.get("openrouter_cost_usd", 0)
    if cost:
        print(f"OpenRouter spend this run: ${cost:.4f}")
    if manifest.get("errors"):
        print(f"{len(manifest['errors'])} model/task errors (see manifest.json)")


if __name__ == "__main__":
    main()
