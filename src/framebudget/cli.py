"""FrameBudget command-line entry point."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from .analysis import summarize_suite
from .compare import compare_suites
from .doctor import EngineFailure, diagnose
from .report import write_comparison_html, write_json
from .runner import run_once
from .schema import InvalidRun, load_runs
from .synthetic import write_synthetic_run


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="framebudget")
    commands = root.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Inspect Godot and graphics availability")
    doctor.add_argument("--godot")
    run = commands.add_parser("run", help="Collect real Godot data")
    run.add_argument("--godot")
    run.add_argument("--workload", choices=("idle", "cpu_nodes", "mesh_draw"), default="cpu_nodes")
    run.add_argument("--objects", type=int, default=100)
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--max-fps", type=int, default=0)
    run.add_argument("--vsync", choices=("disabled", "enabled"), default="disabled")
    run.add_argument("--warmup", type=float, default=5)
    run.add_argument("--duration", type=float, default=15)
    run.add_argument("--repeat", type=int, default=5)
    run.add_argument("--timeout", type=float, default=60)
    run.add_argument("--headless", action="store_true", help="Validate schema only; no performance claim")
    run.add_argument("--out", type=Path, required=True)
    analyze = commands.add_parser("analyze", help="Summarize one run or a run suite")
    analyze.add_argument("input", type=Path)
    analyze.add_argument("--out", type=Path, required=True)
    analyze.add_argument("--hitch-ms", type=float, default=None)
    compare = commands.add_parser("compare", help="Compare compatible suites")
    compare.add_argument("baseline", type=Path)
    compare.add_argument("candidate", type=Path)
    compare.add_argument("--out", type=Path, required=True)
    compare.add_argument("--threshold-percent", type=float, default=10)
    compare.add_argument("--hitch-ms", type=float, default=None)
    demo = commands.add_parser("demo", help="Generate synthetic analysis and HTML")
    demo.add_argument("--synthetic", action="store_true", required=True)
    demo.add_argument("--out", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "doctor":
            print(json.dumps(diagnose(args.godot), indent=2))
        elif args.command == "run":
            if (args.objects < 0 or args.repeat < 1 or args.max_fps < 0
                    or not all(math.isfinite(value) for value in (args.warmup, args.duration, args.timeout))
                    or args.warmup < 0 or args.duration <= 0 or args.timeout <= 0):
                raise InvalidRun("objects, repeat, warmup, duration, timeout or max_fps out of range")
            if args.out.is_file() or (args.out.exists() and any(args.out.iterdir())):
                raise InvalidRun(f"output directory is not empty: {args.out}")
            args.out.mkdir(parents=True, exist_ok=True)
            for index in range(args.repeat):
                path = args.out / f"run-{index + 1:02d}"
                run_once(args.godot, path, workload=args.workload, objects=args.objects,
                         seed=args.seed, warmup=args.warmup, duration=args.duration,
                         headless=args.headless, timeout=args.timeout,
                         max_fps=args.max_fps, vsync=args.vsync)
                print(path)
        elif args.command == "analyze":
            options = {} if args.hitch_ms is None else {"hitch_ms": args.hitch_ms}
            result = summarize_suite(load_runs(args.input), **options)
            write_json(args.out, result)
            print(args.out)
        elif args.command == "compare":
            result = compare_suites(load_runs(args.baseline), load_runs(args.candidate),
                                    args.threshold_percent, args.hitch_ms)
            write_json(args.out / "comparison.json", result)
            write_comparison_html(args.out / "index.html", result)
            print(args.out / "index.html")
            return 1 if result["regression_flagged"] else 0
        elif args.command == "demo":
            base, candidate = args.out / "runs" / "baseline", args.out / "runs" / "candidate"
            if args.out.is_file() or (args.out.exists() and any(args.out.iterdir())):
                raise InvalidRun(f"output directory is not empty: {args.out}")
            for index in range(5):
                write_synthetic_run(base / f"run-{index + 1:02d}", f"synthetic-baseline-{index + 1}")
                write_synthetic_run(candidate / f"run-{index + 1:02d}",
                                    f"synthetic-candidate-{index + 1}", slowdown_ms=3)
            result = compare_suites(load_runs(base), load_runs(candidate), 10)
            write_json(args.out / "comparison.json", result)
            write_comparison_html(args.out / "index.html", result)
            print(args.out / "index.html")
    except InvalidRun as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    except EngineFailure as exc:
        print(f"engine failure: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
