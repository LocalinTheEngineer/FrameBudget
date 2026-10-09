# ADR 0002: Compare repeated frame-time summaries rather than FPS alone

## Decision

Record frame intervals, keep each run separate, and compare the median of
per-run p95 values after five repeats per condition. Report p50 and hitch rate
for each run as supporting context.

## Why

Average FPS can hide slow frames. Pooling all frames can conceal variation
between runs and lets long runs dominate short runs. A per-run p95 is easy to
explain with nearest-rank quantiles; its median reduces one unusually noisy
repeat. Config matching prevents an apparent regression caused by a different
renderer, GPU, resolution, cap or VSync mode.

## Alternative

A paired statistical test or bootstrap interval may eventually be useful,
but it requires a stronger experimental protocol and a documented noise
model. A single FPS delta is simpler but too easy to misinterpret.

## Consequences

The gate is a heuristic, not proof of significance. Five repeats are a
minimum policy, not a measured noise floor. The report retains raw CSV for
inspection and warns when evidence is insufficient.
