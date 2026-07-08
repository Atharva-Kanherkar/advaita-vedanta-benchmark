from __future__ import annotations

import argparse
from pathlib import Path

from harness.judge import judge_run
from harness.report import generate_report, print_report
from harness.runner import run_benchmark


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASKS = ROOT / "tasks"
DEFAULT_RUNS = ROOT / "runs"


def main() -> None:
    parser = argparse.ArgumentParser(description="AdvaitaBench — Advaita Vedānta LLM benchmark")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run subject models on tasks")
    run_p.add_argument("--models", required=True, help="Comma-separated model IDs")
    run_p.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    run_p.add_argument("--output", type=Path, default=DEFAULT_RUNS)
    run_p.add_argument("--system", default="school_pinned", choices=["neutral", "school_pinned", "teacher"])
    run_p.add_argument("--family", default=None, help="Limit to one task family")
    run_p.add_argument("--dry-run", action="store_true")

    judge_p = sub.add_parser("judge", help="Grade responses with rubric judge")
    judge_p.add_argument("--run", type=Path, required=True, help="Run directory")
    judge_p.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    judge_p.add_argument("--judge-model", default="gpt-4.1")
    judge_p.add_argument("--dry-run", action="store_true")

    report_p = sub.add_parser("report", help="Aggregate judged scores")
    report_p.add_argument("--run", type=Path, required=True)
    report_p.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)

    validate_p = sub.add_parser("validate", help="Validate task YAML files")
    validate_p.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)

    args = parser.parse_args()

    if args.command == "run":
        models = [m.strip() for m in args.models.split(",") if m.strip()]
        run_path = run_benchmark(
            tasks_dir=args.tasks,
            models=models,
            output_dir=args.output,
            system_condition=args.system,
            family=args.family,
            dry_run=args.dry_run,
        )
        print(f"Run complete: {run_path}")

    elif args.command == "judge":
        judged = judge_run(args.run, args.tasks, args.judge_model, dry_run=args.dry_run)
        print(f"Judging complete: {judged}")

    elif args.command == "report":
        report = generate_report(args.run, args.tasks)
        print_report(report)
        print(f"Report written: {args.run / 'report.json'}")

    elif args.command == "validate":
        from scripts.validate_tasks import validate

        errors = validate(args.tasks)
        if errors:
            for e in errors:
                print(f"ERROR: {e}")
            raise SystemExit(1)
        print(f"All tasks valid under {args.tasks}")


if __name__ == "__main__":
    main()
