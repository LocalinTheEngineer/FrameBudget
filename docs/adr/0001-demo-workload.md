# ADR 0001: Use a demo workload before a universal profiler plugin

## Decision

Ship a small Godot project with a fixed camera, primitive meshes and three
workloads. Collect raw samples from that project and analyze them offline.

## Why

A user-project plugin would need to control scene state, assets, startup,
physics, camera movement and project settings across many games. That would
make a small regression tool hard to verify. The demo scene makes conditions
visible and reproducible, while the manifest records the settings that can
invalidate a comparison.

## Alternative

A Godot editor plugin could be more convenient for an existing game. It is a
later integration after this data contract and comparison behavior are stable.

## Consequences

FrameBudget currently measures its own demo, not arbitrary game scenes. It can
show how to measure a controlled change but cannot diagnose a user's game by
itself. Fixed seed controls placement, not GPU or scheduling variability.
