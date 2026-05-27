# Collision Detection Repair

## What this is

Particle collision simulation. Loads particle positions from three simulation streams, detects collisions using spatial hashing, resolves collision responses, and generates statistics.

## Environment

- Python 3.11, working dir `/app`, source `/app/runtime/`, output `/app/runtime/output/`
- pytest available globally

## Processing stages

1. **Load** — Read particle position streams from simulation data files.
2. **Hash** — Assign particles to spatial grid cells for broad-phase detection.
3. **Detect** — Check particle pairs in nearby cells for actual collisions.
4. **Resolve** — Compute collision responses and update velocity history.
5. **Report** — Generate collision statistics and summary metrics.

## Symptoms

Some collisions go undetected. Collision response values seem off. Statistics don't match expected particle interaction counts.

## Expected output

- `/app/runtime/output/collisions.json`: list of objects with `pair`(list[str]), `cell`(list[int]), `response_velocity`(float), `restitution`(float)
- `/app/runtime/output/summary.json`: `total_collisions`(int), `unique_pairs`(int), `avg_response_velocity`(float), `max_response_velocity`(float), `cells_with_collisions`(int)

## Key files

| File | Purpose |
|------|---------|
| `runtime/hasher.py` | Spatial hashing and neighbor search |
| `runtime/resolver.py` | Collision response computation |
| `runtime/config.ini` | Grid sizes, physics parameters |
| `runtime/main.py` | Pipeline orchestration |

## Task

Find and fix the bugs causing incorrect collision detection and response calculations. Multiple interacting defects exist across files.
