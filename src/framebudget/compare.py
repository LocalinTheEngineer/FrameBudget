"""Config-compatible, repeat-aware comparison gate."""

from __future__ import annotations

import math

from .analysis import summarize_suite
from .schema import CONFIG_FIELDS, InvalidRun, Run


def compare_suites(baseline: list[Run], candidate: list[Run], threshold_percent: float,
                   hitch_ms: float | None = None) -> dict:
    if not math.isfinite(threshold_percent) or threshold_percent < 0:
        raise InvalidRun("threshold percent must be nonnegative and finite")
    options = {} if hitch_ms is None else {"hitch_ms": hitch_ms}
    base = summarize_suite(baseline, **options)
    cand = summarize_suite(candidate, **options)
    first, second = baseline[0].manifest, candidate[0].manifest
    mismatches = [field for field in CONFIG_FIELDS if first[field] != second[field]]
    if mismatches:
        raise InvalidRun("incompatible configurations: " + ", ".join(mismatches))
    base_p95 = base["median_run_p95_ms"]
    if base_p95 <= 0:
        raise InvalidRun("baseline median p95 is zero")
    delta = cand["median_run_p95_ms"] - base_p95
    percent = delta / base_p95 * 100
    enough = len(baseline) >= 5 and len(candidate) >= 5
    warnings = base["warnings"] + cand["warnings"]
    if not enough:
        warnings.append("Insufficient repeats for a regression gate; result is descriptive only")
    if first["mode"] == "headless":
        warnings.append("Headless validation is not rendered performance evidence")
    if first["mode"] == "synthetic":
        warnings.append("SYNTHETIC data verifies the analyzer only")
    return {
        "schema_version": 1, "baseline": base, "candidate": cand,
        "environment_compatible": True, "delta_ms": delta, "delta_percent": percent,
        "threshold_percent": threshold_percent, "enough_repeats": enough,
        "regression_flagged": enough and percent > threshold_percent,
        "warnings": warnings,
    }
