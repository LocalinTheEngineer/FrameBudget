import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def _call(self, *args):
        return subprocess.run([sys.executable, "-m", "framebudget.cli", *map(str, args)],
                              capture_output=True, text=True, timeout=30)

    def test_synthetic_demo_and_invalid_compare(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "demo"
            result = self._call("demo", "--synthetic", "--out", out)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out / "index.html").is_file())
            comparison = self._call("compare", out / "runs" / "baseline",
                                    out / "runs" / "candidate", "--out", out / "gate")
            self.assertEqual(comparison.returncode, 1, comparison.stderr)
            missing = self._call("analyze", out / "missing", "--out", out / "x.json")
            self.assertEqual(missing.returncode, 2)

    def test_missing_engine(self):
        result = self._call("doctor", "--godot", "Z:/not/a/godot.exe")
        self.assertEqual(result.returncode, 3)

    @unittest.skipUnless(os.environ.get("GODOT_PATH"), "GODOT_PATH not set")
    def test_real_godot_headless_schema(self):
        with tempfile.TemporaryDirectory(prefix="framebudget space ") as directory:
            out = Path(directory) / "run suite"
            result = self._call("run", "--godot", os.environ["GODOT_PATH"],
                                "--headless", "--warmup", ".1", "--duration", ".2",
                                "--repeat", "1", "--out", out)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = self._call("analyze", out, "--out", out / "summary.json")
            self.assertEqual(result.returncode, 0, result.stderr)
