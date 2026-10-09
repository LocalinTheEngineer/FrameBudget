# Learning path

Each stage has one small exercise. You can do it after the implementation is
running; no answer is required to use FrameBudget.

## 1. Contract and analyzer

- **Problem:** Raw frame data can contain startup frames or bad values.
- **Decision:** Validate a strict CSV/manifest pair and exclude warmup.
- **Alternative:** Trust the exporter and calculate directly from every row.
- **Failure example:** A duplicate timestamp or `NaN` would make a percentile misleading.
- **Try:** Change `nearest_rank` in `src/framebudget/analysis.py` to compute p90 too, then add a known-series test.
- **Check:** Why does `ceil(q*N)-1` select the last item for p95 in a four-value series?

## 2. Godot exporter

- **Problem:** A frame interval and a workload's CPU time answer different questions.
- **Decision:** Time consecutive `_process` entry ticks and the update function separately.
- **Alternative:** Use only Godot's FPS monitor.
- **Failure example:** Measuring the whole frame as workload CPU would wrongly attribute render wait to the script.
- **Try:** Add a harmless calculation inside `cpu_nodes.gd` and inspect both CSV columns.
- **Check:** Why does the first `_process` entry have no interval?

## 3. Runner and doctor

- **Problem:** A benchmark child can hang or fail before writing samples.
- **Decision:** Launch with argv, enforce a timeout, kill the child tree and validate output.
- **Alternative:** Invoke one shell command string and assume exit 0 means valid data.
- **Failure example:** A script parse error may still leave a Godot process or incomplete directory.
- **Try:** Set `--timeout 0.01` and inspect the exit code and log.
- **Check:** Why is `--headless` useful for CI but unsuitable for rendered performance?

## 4. Workloads

- **Problem:** Changes in scene content can masquerade as performance changes.
- **Decision:** Fix camera and seeded placement; vary one workload parameter at a time.
- **Alternative:** Use a random scene on every run.
- **Failure example:** Different visible objects would confound a mesh comparison.
- **Try:** Run `mesh_draw` with 50 and 500 objects and inspect both manifests.
- **Check:** Why does 500 mesh instances not necessarily mean 500 draw calls?

## 5. Comparison and report

- **Problem:** One FPS number hides slow frames and run-to-run noise.
- **Decision:** Compare median per-run p95 only for matching configurations.
- **Alternative:** Pool all frames from every repeat.
- **Failure example:** A resolution mismatch can look like a code regression.
- **Try:** Change one candidate manifest's resolution, recompute its hash and run compare.
- **Check:** Why is a three-repeat result descriptive rather than a gate verdict?

## 6. CI and smoke

- **Problem:** CI hosts have no reliable rendering environment.
- **Decision:** Run Python tests and a separate Godot headless schema smoke in CI.
- **Alternative:** Set a hardware performance gate on a shared runner.
- **Failure example:** Contended CI CPU changes frame intervals without a code change.
- **Try:** Run the headless smoke locally with `GODOT_PATH` and inspect `mode`.
- **Check:** Which test would you need to perform before claiming GPU performance?

## 7. Noise floor

- **Problem:** A threshold is meaningless without seeing baseline variation.
- **Decision:** Collect two separate baseline suites with identical settings before interpreting a candidate.
- **Alternative:** Pick 10% as a universal noise threshold.
- **Failure example:** A machine with 12% normal run variation could trip a 10% gate.
- **Try:** Collect two five-repeat rendered baseline suites and compare them; keep raw data and both manifests.
- **Check:** Would a small p95 delta with a large hitch-rate change need investigation?
