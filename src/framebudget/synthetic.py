"""Deterministic sample generator for the analyzer demo only."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .schema import CSV_FIELDS, config_hash


def write_synthetic_run(path: Path, run_id: str, slowdown_ms: float = 0) -> None:
    path.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1, "run_id": run_id,
        "utc_time": datetime.now(timezone.utc).isoformat(),
        "tool_version": __version__, "tool_commit": "unknown", "engine_version": "synthetic",
        "os": "synthetic", "renderer": "synthetic", "device_info": "unknown",
        "resolution": [640, 360], "vsync": "disabled", "max_fps": 0, "seed": 42,
        "workload": "cpu_nodes", "object_count": 100, "warmup_s": 0.1,
        "duration_s": 1.0, "mode": "synthetic", "camera_path": "fixed", "shadows": False,
    }
    manifest["config_hash"] = config_hash(manifest)
    (path / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    time_us = 0
    with (path / "samples.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(CSV_FIELDS)
        for index in range(110):
            phase = "warmup" if index < 10 else "measure"
            interval = 16.0 + (index % 10) * .2 + (slowdown_ms if phase == "measure" else 0)
            time_us += round(interval * 1000)
            writer.writerow((1, run_id, index, phase, time_us, interval, 1.0))
