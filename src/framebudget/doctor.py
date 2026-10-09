"""Environment checks for the optional Godot execution stage."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


class EngineFailure(RuntimeError):
    pass


def resolve_godot(value: str | None) -> Path:
    candidate = value or shutil.which("godot") or shutil.which("godot4")
    if not candidate:
        raise EngineFailure("Godot executable not found; pass --godot PATH")
    path = Path(candidate).expanduser().resolve()
    if not path.is_file():
        raise EngineFailure(f"Godot executable not found: {path}")
    return path


def graphics_available() -> bool:
    if sys.platform == "win32":
        try:
            import ctypes
            handle = ctypes.windll.user32.GetDC(0)
            if handle:
                ctypes.windll.user32.ReleaseDC(0, handle)
            return bool(handle)
        except (AttributeError, OSError):
            return False
    if sys.platform == "darwin":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def diagnose(godot: str | None) -> dict:
    path = resolve_godot(godot)
    try:
        result = subprocess.run([str(path), "--version"], capture_output=True, text=True,
                                timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EngineFailure(f"Could not inspect Godot: {exc}") from exc
    if result.returncode != 0 or not result.stdout.strip():
        raise EngineFailure(f"Godot version check failed: {result.stderr.strip()}")
    if not result.stdout.strip().startswith("4."):
        raise EngineFailure(f"Godot 4.x is required, found: {result.stdout.strip()}")
    return {"godot": str(path), "version": result.stdout.strip(),
            "graphics_available": graphics_available(),
            "headless": "validation only; no rendered performance claim"}
