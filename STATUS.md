# Project status

## Implemented

- Strict versioned CSV/manifest loader, nearest-rank p50/p95, hitch count/rate and warmup exclusion.
- Godot 3D demo with idle, CPU-node and separate-mesh workloads; fixed seed and camera.
- Godot exporter for CSV, manifest and separately sampled engine process monitor.
- Python doctor/runner with timeout, process-tree cleanup and output validation.
- Compatible, repeat-aware comparison and standalone escaped HTML/JSON reports.
- Synthetic controlled slowdown demo and Python tests.

## Verification record

- Local Windows, Python 3.12.10, Godot 4.7.2, NVIDIA RTX 4050 Laptop GPU.
- Godot headless schema smoke passed for `cpu_nodes` and `mesh_draw` with very short durations.
- A short `idle` rendered smoke produced a manifest and CSV at 640×360. This is
  functionality verification, not a trustworthy performance or noise-floor run.
- GitHub Actions workflow is authored but has not run on GitHub.

## Open work and limitations

- An exploratory two-baseline rendered noise-floor experiment was performed
  with five repeats per set, 0.5 s warmup and 1 s collection per repeat.
  Median per-run p95 was 1.013 ms vs 1.007 ms (delta -0.5923%); no 10% gate
  violation. Raw data is in `examples/noise-2026-10-09/`. These short runs do
  not establish a reliable threshold. The default 5 s + 15 s protocol remains
  untested in a full two-baseline experiment.
- No GPU frame timer is available; `gpu_frame_ms` is null/unsupported.
- This is a demo benchmark kit, not a plugin for arbitrary Godot projects.
