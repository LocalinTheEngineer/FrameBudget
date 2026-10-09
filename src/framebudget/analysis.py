"""Nearest-rank frame-time summaries; warmup never enters statistics."""

from __future__ import annotations

import math
import statistics

from .schema import InvalidRun, Run

DEFAULT_HITCH_MS = 1000 / 60 * 2


def nearest_rank(values: list[float], quantile: float) -> float:
    if not values or not 0 < quantile <= 1:
        raise InvalidRun("quantile requires nonempty data and 0 < q <= 1")
    ordered = sorted(values)
    return ordered[math.ceil(quantile * len(ordered)) - 1]


def summarize(run: Run, hitch_ms: float = DEFAULT_HITCH_MS) -> dict:
    if not math.isfinite(hitch_ms) or hitch_ms <= 0:
        raise InvalidRun("hitch threshold must be positive and finite")
    measured = [sample for sample in run.samples if sample.phase == "measure"]
    if not measured:
        raise InvalidRun("empty measurement run")
    intervals = [sample.frame_interval_ms for sample in measured]
    cpu = [sample.workload_cpu_ms for sample in measured]
    hitches = sum(value > hitch_ms for value in intervals)
    return {
        "run_id": run.manifest["run_id"], "source": str(run.path),
        "mode": run.manifest["mode"], "config_hash": run.manifest["config_hash"],
        "valid": True, "frame_count": len(measured),
        "excluded_warmup_count": len(run.samples) - len(measured),
        "p50_ms": nearest_rank(intervals, .5), "p95_ms": nearest_rank(intervals, .95),
        "hitch_threshold_ms": hitch_ms, "hitch_count": hitches,
        "hitch_rate": hitches / len(measured),
        "workload_cpu_p50_ms": nearest_rank(cpu, .5),
        "workload_cpu_p95_ms": nearest_rank(cpu, .95),
        "gpu_frame_ms": None,
    }


def summarize_suite(runs: list[Run], hitch_ms: float = DEFAULT_HITCH_MS) -> dict:
    if not runs:
        raise InvalidRun("empty suite")
    hashes = {run.manifest["config_hash"] for run in runs}
    if len(hashes) != 1:
        raise InvalidRun("suite contains incompatible configurations")
    per_run = [summarize(run, hitch_ms) for run in runs]
    return {
        "schema_version": 1, "config": runs[0].manifest,
        "run_count": len(runs), "runs": per_run,
        "median_run_p95_ms": statistics.median(item["p95_ms"] for item in per_run),
        "warnings": ["Fewer than five repeats: insufficient evidence for a stable gate"]
        if len(runs) < 5 else [],
    }
