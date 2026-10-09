"""Standalone escaped HTML, without scripts, CDN or external styles."""

from __future__ import annotations

import html
import json
from pathlib import Path


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_comparison_html(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    def escape(value: object) -> str:
        return html.escape(str(value), quote=True)
    mode = result["baseline"]["config"]["mode"]
    rows = []
    for label in ("baseline", "candidate"):
        for item in result[label]["runs"]:
            raw = (Path(item["source"]) / "samples.csv").resolve().as_uri()
            rows.append("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in
                        (label, item["run_id"], item["frame_count"], item["p50_ms"],
                         item["p95_ms"], item["hitch_count"], item["hitch_rate"])) +
                        f'<td><a href="{escape(raw)}">CSV</a></td></tr>')
    config = result["baseline"]["config"]
    warnings = "".join(f"<li>{escape(item)}</li>" for item in result["warnings"])
    badge = "<strong>SYNTHETIC — NOT MEASURED</strong>" if mode == "synthetic" else ""
    path.write_text(f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>FrameBudget comparison</title><style>
body{{font:16px system-ui;max-width:980px;margin:2rem auto;padding:0 1rem;color:#17202a}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #bbb;padding:.5rem;text-align:left}}
th{{background:#eef2f5}}code{{overflow-wrap:anywhere}}strong{{color:#a20}}
</style><h1>FrameBudget comparison</h1>{badge}
<h2>Workload and configuration</h2><pre>{escape(json.dumps({k: config[k] for k in ('workload','object_count','seed','resolution','renderer','vsync','max_fps','warmup_s','duration_s','mode')}, indent=2))}</pre>
<h2>Environment compatibility</h2><p>Compatible: {escape(result['environment_compatible'])}. Matching configuration is required.</p>
<h2>Per-run results</h2><table><thead><tr><th>Set</th><th>Run</th><th>Frames</th><th>p50 ms</th><th>p95 ms</th><th>Hitches</th><th>Hitch rate</th><th>Raw data</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Aggregation</h2><p>Median of per-run p95: baseline {escape(result['baseline']['median_run_p95_ms'])} ms; candidate {escape(result['candidate']['median_run_p95_ms'])} ms. Delta {escape(result['delta_ms'])} ms ({escape(result['delta_percent'])}%). Gate: {escape(result['regression_flagged'])} at {escape(result['threshold_percent'])}%.</p>
<h2>Metric definitions</h2><p>Frame interval is time between consecutive _process entries. p50/p95 use nearest rank: sorted index ceil(q × N) − 1. Hitch means interval strictly greater than the displayed threshold, divided by valid measurement frames. Workload CPU time covers only the custom update. GPU time is unsupported.</p>
<h2>Warnings</h2><ul>{warnings}</ul>
<h2>Limitations</h2><p>One target budget breach does not prove visible stutter. Driver and scheduling variance remain. Headless and synthetic data are not rendered performance measurements.</p>
<h2>Reproduction</h2><p>Run the same FrameBudget command with matching configuration and five repeats per set; inspect linked CSV files and manifests.</p>
</html>""", encoding="utf-8")
