import tempfile
import unittest
from pathlib import Path

from framebudget.analysis import nearest_rank, summarize
from framebudget.schema import InvalidRun, load_run
from framebudget.synthetic import write_synthetic_run


class AnalysisTests(unittest.TestCase):
    def test_nearest_rank_and_empty(self):
        self.assertEqual(nearest_rank([9, 1, 5, 3], .5), 3)
        self.assertEqual(nearest_rank([9, 1, 5, 3], .95), 9)
        with self.assertRaises(InvalidRun):
            nearest_rank([], .95)

    def test_warmup_hitch_boundary_and_repeatability(self):
        with tempfile.TemporaryDirectory() as directory:
            write_synthetic_run(Path(directory), "demo")
            run = load_run(directory)
            first = summarize(run, hitch_ms=16.0)
            self.assertEqual(first, summarize(run, hitch_ms=16.0))
            self.assertEqual(first["frame_count"], 100)
            self.assertEqual(first["excluded_warmup_count"], 10)
            self.assertEqual(first["hitch_count"], 90)
            self.assertEqual(first["hitch_rate"], .9)

    def test_corrupt_data_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            write_synthetic_run(path, "demo")
            original = (path / "samples.csv").read_text()
            for bad in ("nan", "inf", "-1", ""):
                (path / "samples.csv").write_text(original.replace(",16.0,1.0", f",{bad},1.0", 1))
                with self.subTest(bad=bad), self.assertRaises(InvalidRun):
                    load_run(path)
            rows = original.splitlines()
            rows[2] = rows[1].replace(",0,warmup,", ",1,warmup,")
            (path / "samples.csv").write_text("\n".join(rows) + "\n")
            with self.assertRaises(InvalidRun):
                load_run(path)
