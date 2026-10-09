import json
import tempfile
import unittest
from pathlib import Path

from framebudget.compare import compare_suites
from framebudget.report import write_comparison_html
from framebudget.schema import InvalidRun, config_hash, load_run, load_runs
from framebudget.synthetic import write_synthetic_run


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / "base"
        self.candidate = self.root / "candidate"
        for index in range(5):
            write_synthetic_run(self.base / f"run-{index}", f"base-{index}")
            write_synthetic_run(self.candidate / f"run-{index}", f"candidate-{index}", 3)

    def _edit_manifest(self, key, value):
        path = self.candidate / "run-0" / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest[key] = value
        manifest["config_hash"] = config_hash(manifest)
        path.write_text(json.dumps(manifest))

    def test_controlled_slowdown_flags_regression(self):
        result = compare_suites(load_runs(self.base), load_runs(self.candidate), 10)
        self.assertTrue(result["regression_flagged"])
        self.assertGreater(result["delta_percent"], 10)
        self.assertEqual(len(result["baseline"]["runs"]), 5)

    def test_single_run_is_descriptive(self):
        result = compare_suites([load_run(self.base / "run-0")],
                                [load_run(self.candidate / "run-0")], 10)
        self.assertFalse(result["regression_flagged"])
        self.assertFalse(result["enough_repeats"])

    def test_mismatched_conditions_rejected(self):
        cases = {"renderer": "other", "vsync": "enabled", "resolution": [800, 600],
                 "object_count": 101, "mode": "headless", "device_info": "other GPU"}
        for key, value in cases.items():
            with self.subTest(key=key):
                self._edit_manifest(key, value)
                with self.assertRaises(InvalidRun):
                    compare_suites(load_runs(self.base), load_runs(self.candidate), 10)
                # Restore to isolate the next mismatch.
                self._edit_manifest(key, load_run(self.base / "run-0").manifest[key])

    def test_revision_metadata_may_differ(self):
        self._edit_manifest("tool_commit", "candidate-revision")
        result = compare_suites(load_runs(self.base), load_runs(self.candidate), 10)
        self.assertTrue(result["environment_compatible"])

    def test_bad_schema_empty_and_duplicate_timestamp(self):
        path = self.base / "run-0"
        manifest_path = path / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["schema_version"] = 99
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(InvalidRun, "unsupported schema"):
            load_run(path)
        manifest["schema_version"] = 1
        manifest_path.write_text(json.dumps(manifest))
        csv_path = path / "samples.csv"
        original = csv_path.read_text()
        csv_path.write_text(original.splitlines()[0] + "\n")
        with self.assertRaisesRegex(InvalidRun, "empty"):
            load_run(path)
        lines = original.splitlines()
        fields = lines[2].split(",")
        fields[4] = lines[1].split(",")[4]
        lines[2] = ",".join(fields)
        csv_path.write_text("\n".join(lines) + "\n")
        with self.assertRaisesRegex(InvalidRun, "nonmonotonic"):
            load_run(path)

    def test_phase_order_and_malformed_header(self):
        path = self.base / "run-0" / "samples.csv"
        original = path.read_text()
        lines = original.splitlines()
        parts = lines[-1].split(",")
        parts[3] = "warmup"
        lines[-1] = ",".join(parts)
        path.write_text("\n".join(lines) + "\n")
        with self.assertRaisesRegex(InvalidRun, "warmup after"):
            load_run(path.parent)
        path.write_text(original.replace("frame_interval_ms", "fps", 1))
        with self.assertRaisesRegex(InvalidRun, "unexpected header"):
            load_run(path.parent)

    def test_html_escapes_untrusted_run_id(self):
        result = compare_suites(load_runs(self.base), load_runs(self.candidate), 10)
        result["baseline"]["runs"][0]["run_id"] = '<script>alert("x")</script>'
        output = self.root / "report.html"
        write_comparison_html(output, result)
        content = output.read_text()
        self.assertNotIn('<script>alert', content)
        self.assertIn('&lt;script&gt;', content)
        self.assertIn("SYNTHETIC", content)
