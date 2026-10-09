# FrameBudget

FrameBudget is an offline benchmark kit for solo Godot developers. It runs one
controlled 3D scene, records per-frame intervals and workload CPU time, and
compares repeated runs. It is a demo workload, not a universal profiler plugin.

## Requirements and clean install

- Python 3.11 or newer. Runtime dependencies: none. `pyproject.toml` pins the
  setuptools build backend; `requirements.lock` records the empty runtime set.
- Godot 4.7.2 for collection. The official Godot 4.x binary is optional for
  `analyze`, `compare`, and `demo`. For rendered runs, a graphics session,
  supported OpenGL driver, and suitable hardware are required.

```sh
python -m venv .venv
# Activate .venv using your shell's standard command.
python -m pip install -e .
python -m pip install -r requirements-dev.lock  # optional lint
python -m unittest discover -s tests -p 'test_*.py' -v
ruff check .                                     # if installed
```

The commands below use `python -m framebudget.cli`; the installed
`framebudget` console command is equivalent. Quote paths containing spaces.

## Try the analysis without Godot

```sh
python -m framebudget.cli demo --synthetic --out reports/demo
python -m framebudget.cli analyze reports/demo/runs/baseline --out reports/base.json
python -m framebudget.cli compare reports/demo/runs/baseline reports/demo/runs/candidate --out reports/check --threshold-percent 10
```

Open `reports/demo/index.html` locally. It says **SYNTHETIC — NOT MEASURED**.
The controlled synthetic candidate adds 3 ms to each measurement interval;
the last `compare` command intentionally exits 1 because the regression gate
is violated.

## Collect Godot data

```sh
python -m framebudget.cli doctor --godot "/path/to/Godot_4.7.2"
python -m framebudget.cli run --godot "/path/to/Godot_4.7.2" --workload cpu_nodes --objects 500 --seed 42 --out benchmarks/baseline
python -m framebudget.cli run --godot "/path/to/Godot_4.7.2" --workload cpu_nodes --objects 500 --seed 42 --out benchmarks/candidate
python -m framebudget.cli analyze benchmarks/baseline --out reports/baseline.json
python -m framebudget.cli compare benchmarks/baseline benchmarks/candidate --out reports/comparison --threshold-percent 10
```

Each `run` collects five independent repeats by default, each with five seconds
of warmup and 15 seconds of measurement. Use `--repeat`, `--warmup`, and
`--duration` for exploratory work. Use `--headless` only to validate scene and
data flow; its interval is not a rendered performance result. The default
benchmark is uncapped with VSync disabled. It may use more power and produce
very high FPS. Use `--max-fps 60` or `--vsync enabled` for separate experiments;
those options change the configuration identity. Keep the same power profile, display, graphics driver and
background load across sets. A 60 Hz budget is 16.667 ms, but crossing it
alone does not prove visible stutter.

The three workloads are `idle` (eight fixed boxes), `cpu_nodes` (sin/cos
transforms for N boxes), and `mesh_draw` (N separate static mesh instances).
The same seed gives repeatable placement and count. It does not make GPU,
driver, physics or OS scheduling deterministic. `mesh_draw` does not claim N
draw calls; the engine's actual draw count is not measured here.

## Data and statistics

Every run directory has `manifest.json`, `samples.csv`,
`engine_monitor.jsonl` and `godot.log`. The Python runner seals the manifest's
SHA-256 `config_hash` after Godot exits and validates the CSV. Direct Godot
execution leaves a pending hash and is not a valid analyzed run until sealed.

`frame_interval_ms` is the monotonic interval between consecutive `_process`
entries. `workload_cpu_ms` times only the custom workload update. The optional
`engine_monitor.jsonl` samples Godot's `Performance.TIME_PROCESS` roughly once
per second; it is engine process time for a completed frame, not a second copy
of frame interval. The manifest records this sampling period. GPU frame time
is `null` and unsupported. These metrics must not be interchanged.

Warmup rows remain in raw CSV but are excluded from statistics. The first
entry has no preceding interval and is skipped. p50 and p95 use **nearest
rank**: sort N valid measurement intervals and select zero-based index
`ceil(q*N)-1`. A hitch is an interval strictly greater than the configured
threshold (default 33.333 ms), divided by the number of valid measurement
frames. Invalid, nonfinite, negative, duplicate-timestamp and malformed rows
fail validation; they are never silently converted to zero.

The comparison uses the **median of each run's p95**, not a pool of all frames.
A regression is flagged when its percentage rise is greater than the gate
threshold and both sets contain at least five repeats. Fewer repeats are
descriptive only. This is an engineering gate, not a significance test.
Baseline p95 of zero is invalid. Renderer, device, OS, resolution, VSync,
max FPS, mode, workload, seed, object count, duration, camera path and shadows
must match. Run IDs, timestamps, tool commit and tool version may differ.
Headless, rendered and synthetic runs cannot be mixed.

An exploratory rendered noise experiment is included in
`examples/noise-2026-10-09/`: two baseline sets of five 0.5 s warmup + 1 s
measurement repeats on Windows with an RTX 4050. The median per-run p95 was
1.013 ms vs 1.007 ms (−0.5923%). The raw files are the evidence; this short
experiment does not establish a general noise threshold or replace the
default 5 s + 15 s protocol.

Exit codes: 0 valid/no flagged regression; 1 regression gate violation;
2 invalid input or incompatible data; 3 environment or engine failure.

## Reproduction and limitations

The report is standalone HTML with no CDN. Its per-run table links to raw CSV.
Copy both suite directories and their manifests together; local file links
resolve only while the source files remain at the reported paths. The fixed
camera and primitive scene have no third-party assets. `docs/learning.md`
walks through each implementation stage. `docs/adr/` records architectural
choices. See `STATUS.md` for what was actually checked locally and in CI.

Godot's [monotonic tick API](https://docs.godotengine.org/en/stable/classes/class_time.html),
[Performance monitors](https://docs.godotengine.org/en/stable/classes/class_performance.html),
and [headless command line](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html)
describe the engine APIs used here.
