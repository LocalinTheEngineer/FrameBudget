import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from framebudget.doctor import EngineFailure
from framebudget.runner import run_once


class RunnerTests(unittest.TestCase):
    def _run_with_child(self, child):
        with tempfile.TemporaryDirectory(prefix="framebudget path with spaces ") as directory:
            with patch("framebudget.runner.resolve_godot", return_value=Path(directory) / "Godot binary.exe"):
                with patch("framebudget.runner.subprocess.Popen", return_value=child) as launch:
                    with self.assertRaises(EngineFailure):
                        run_once("ignored", Path(directory) / "output dir", workload="idle",
                                 objects=8, seed=42, warmup=.1, duration=.2,
                                 headless=True, timeout=1)
                    argv = launch.call_args.args[0]
                    self.assertEqual(argv[0], str(Path(directory) / "Godot binary.exe"))
                    self.assertIn(str(Path(directory) / "output dir"), argv)

    def test_nonzero_engine_exit(self):
        child = Mock()
        child.communicate.return_value = ("", "failed")
        child.returncode = 7
        self._run_with_child(child)

    def test_timeout_cleans_child(self):
        child = Mock()
        child.communicate.side_effect = subprocess.TimeoutExpired("godot", 1)
        child.pid = 12345
        with patch("framebudget.runner._terminate_tree") as cleanup:
            self._run_with_child(child)
            cleanup.assert_called_once_with(child)
