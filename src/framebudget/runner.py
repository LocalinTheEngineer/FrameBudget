"""Godot child process lifecycle, output validation and manifest sealing."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

from .doctor import EngineFailure, graphics_available, resolve_godot
from .schema import InvalidRun, config_hash, load_run

PROJECT = Path(__file__).resolve().parents[2] / "godot"


def _terminate_tree(process: subprocess.Popen) -> None:
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       capture_output=True, check=False)
    else:
        import signal
        os.killpg(process.pid, signal.SIGKILL)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def run_once(godot: str | None, path: Path, *, workload: str, objects: int, seed: int,
             warmup: float, duration: float, headless: bool, timeout: float,
             max_fps: int = 0, vsync: str = "disabled") -> Path:
    executable = resolve_godot(godot)
    if not headless and not graphics_available():
        raise EngineFailure("No graphics session found; use --headless for schema validation")
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=False)
    run_id = uuid.uuid4().hex
    args = [str(executable)]
    if headless:
        args.append("--headless")
    args.extend(["--path", str(PROJECT), "--", "--out", str(path), "--workload", workload,
                 "--objects", str(objects), "--seed", str(seed), "--warmup", str(warmup),
                 "--duration", str(duration), "--run-id", run_id,
                 "--mode", "headless" if headless else "rendered",
                 "--max-fps", str(max_fps), "--vsync", vsync])
    try:
        child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, start_new_session=True)
        try:
            stdout, stderr = child.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            _terminate_tree(child)
            raise EngineFailure(f"Godot timed out after {timeout}s") from exc
    except OSError as exc:
        raise EngineFailure(f"Could not start Godot: {exc}") from exc
    (path / "godot.log").write_text(stdout + stderr, encoding="utf-8")
    if child.returncode != 0 or "SCRIPT ERROR:" in stderr or "ERROR:" in stderr:
        raise EngineFailure(f"Godot failed (exit {child.returncode}); see {path / 'godot.log'}")
    try:
        manifest_path = path / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("run_id") != run_id:
            raise InvalidRun("Godot output run_id mismatch")
        manifest["config_hash"] = config_hash(manifest)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        load_run(path)
    except (OSError, json.JSONDecodeError, KeyError, InvalidRun) as exc:
        raise EngineFailure(f"Invalid Godot output: {exc}") from exc
    return path
