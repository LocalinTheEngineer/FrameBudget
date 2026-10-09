# Exploratory rendered baseline noise, 2026-10-09

Two independently launched suites, each containing five rendered runs of the
same `cpu_nodes` configuration. Every run used 100 objects, seed 42, 640×360,
OpenGL Compatibility, VSync disabled, uncapped, 0.5 s warmup and 1 s measure.
Host: Windows, Godot 4.7.2, NVIDIA GeForce RTX 4050 Laptop GPU.

Per-run p95 values (ms):

- Baseline A: 1.107, 1.019, 0.984, 1.002, 1.013. Median 1.013.
- Baseline B: 1.007, 0.970, 1.021, 0.901, 1.016. Median 1.007.

Delta: −0.006 ms (−0.5923%). The configured 10% gate did not flag a
regression. This is a short local exploration, not a stable noise-floor
estimate. Rerun the default 5 s warmup + 15 s measurement protocol before
choosing a project threshold. The manifests, raw CSV, monitor JSONL and logs
for all ten runs are included in this directory.

```sh
python -m framebudget.cli compare examples/noise-2026-10-09/noise-baseline-a examples/noise-2026-10-09/noise-baseline-b --out reports/noise --threshold-percent 10
```
