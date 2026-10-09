"""Strict on-disk run contract and compatibility identity."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
CSV_FIELDS = ("schema_version", "run_id", "frame_index", "phase", "time_us",
              "frame_interval_ms", "workload_cpu_ms")
CONFIG_FIELDS = ("engine_version", "os", "renderer", "device_info", "resolution", "vsync",
                 "max_fps", "seed", "workload", "object_count", "warmup_s", "duration_s",
                 "mode", "camera_path", "shadows")
REQUIRED_MANIFEST = ("schema_version", "run_id", "utc_time", "tool_version", "tool_commit",
                     *CONFIG_FIELDS, "config_hash")


class InvalidRun(ValueError):
    """The input is corrupt, unsupported or cannot be compared."""


def config_hash(manifest: dict) -> str:
    payload = {key: manifest[key] for key in CONFIG_FIELDS}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _finite_number(value: object, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise InvalidRun(f"{field}: expected a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidRun(f"{field}: expected a finite number") from exc
    if not math.isfinite(result) or (positive and result <= 0) or result < 0:
        raise InvalidRun(f"{field}: expected {'positive' if positive else 'nonnegative'} finite number")
    return result


@dataclass(frozen=True)
class Sample:
    frame_index: int
    phase: str
    time_us: int
    frame_interval_ms: float
    workload_cpu_ms: float


@dataclass(frozen=True)
class Run:
    path: Path
    manifest: dict
    samples: tuple[Sample, ...]


def load_run(path: Path | str) -> Run:
    path = Path(path)
    try:
        manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidRun(f"manifest.json: {exc}") from exc
    if not isinstance(manifest, dict):
        raise InvalidRun("manifest.json: expected object")
    missing = [key for key in REQUIRED_MANIFEST if key not in manifest]
    if missing:
        raise InvalidRun(f"manifest.json: missing {', '.join(missing)}")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != SCHEMA_VERSION:
        raise InvalidRun("manifest.json: unsupported schema_version")
    if not isinstance(manifest["run_id"], str) or not manifest["run_id"]:
        raise InvalidRun("manifest.json: invalid run_id")
    if manifest["mode"] not in ("rendered", "headless", "synthetic"):
        raise InvalidRun("manifest.json: invalid mode")
    if manifest["workload"] not in ("idle", "cpu_nodes", "mesh_draw"):
        raise InvalidRun("manifest.json: invalid workload")
    try:
        timestamp = datetime.fromisoformat(manifest["utc_time"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise InvalidRun("manifest.json: invalid utc_time") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() != timezone.utc.utcoffset(timestamp):
        raise InvalidRun("manifest.json: utc_time must be UTC")
    for key in ("tool_version", "tool_commit", "engine_version", "os", "renderer",
                "device_info", "camera_path"):
        if not isinstance(manifest[key], str) or not manifest[key]:
            raise InvalidRun(f"manifest.json: invalid {key}")
    if manifest["vsync"] not in ("disabled", "enabled"):
        raise InvalidRun("manifest.json: invalid vsync")
    if (not isinstance(manifest["resolution"], list) or len(manifest["resolution"]) != 2
            or any(type(value) is not int or value < 0 for value in manifest["resolution"])):
        raise InvalidRun("manifest.json: invalid resolution")
    if manifest["mode"] == "rendered" and any(value == 0 for value in manifest["resolution"]):
        raise InvalidRun("manifest.json: rendered resolution must be positive")
    if type(manifest["max_fps"]) is not int or manifest["max_fps"] < 0:
        raise InvalidRun("manifest.json: invalid max_fps")
    if type(manifest["seed"]) is not int or type(manifest["shadows"]) is not bool:
        raise InvalidRun("manifest.json: invalid seed or shadows")
    if manifest["config_hash"] != config_hash(manifest):
        raise InvalidRun("manifest.json: config_hash mismatch")
    for key in ("warmup_s", "duration_s"):
        _finite_number(manifest[key], key, positive=key == "duration_s")
    if type(manifest["object_count"]) is not int or manifest["object_count"] < 0:
        raise InvalidRun("manifest.json: invalid object_count")
    samples: list[Sample] = []
    try:
        with (path / "samples.csv").open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream, strict=True)
            if tuple(reader.fieldnames or ()) != CSV_FIELDS:
                raise InvalidRun("samples.csv: unexpected header")
            previous_time = -1
            previous_index = -1
            for line, row in enumerate(reader, start=2):
                if None in row or None in row.values():
                    raise InvalidRun(f"samples.csv:{line}: malformed row")
                try:
                    version = int(row["schema_version"])
                    index = int(row["frame_index"])
                    time_us = int(row["time_us"])
                except ValueError as exc:
                    raise InvalidRun(f"samples.csv:{line}: invalid integer") from exc
                if version != SCHEMA_VERSION or row["run_id"] != manifest["run_id"]:
                    raise InvalidRun(f"samples.csv:{line}: schema or run_id mismatch")
                if row["phase"] not in ("warmup", "measure"):
                    raise InvalidRun(f"samples.csv:{line}: invalid phase")
                if index <= previous_index or time_us <= previous_time or time_us < 0:
                    raise InvalidRun(f"samples.csv:{line}: nonmonotonic index or timestamp")
                interval = _finite_number(row["frame_interval_ms"], "frame_interval_ms", positive=True)
                cpu = _finite_number(row["workload_cpu_ms"], "workload_cpu_ms")
                samples.append(Sample(index, row["phase"], time_us, interval, cpu))
                previous_time, previous_index = time_us, index
    except (OSError, csv.Error) as exc:
        raise InvalidRun(f"samples.csv: {exc}") from exc
    if not samples or not any(sample.phase == "measure" for sample in samples):
        raise InvalidRun("samples.csv: empty measurement run")
    seen_measure = False
    for sample in samples:
        if sample.phase == "measure":
            seen_measure = True
        elif seen_measure:
            raise InvalidRun("samples.csv: warmup after measurement")
    return Run(path, manifest, tuple(samples))


def load_runs(path: Path | str) -> list[Run]:
    path = Path(path)
    if (path / "manifest.json").is_file():
        return [load_run(path)]
    if not path.is_dir():
        raise InvalidRun(f"run path does not exist: {path}")
    directories = sorted(child for child in path.iterdir() if (child / "manifest.json").is_file())
    if not directories:
        raise InvalidRun(f"no runs found in {path}")
    runs = [load_run(child) for child in directories]
    if len({run.manifest["run_id"] for run in runs}) != len(runs):
        raise InvalidRun("duplicate run_id in suite")
    return runs
