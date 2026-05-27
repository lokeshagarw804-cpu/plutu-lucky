# Collision Detection Repair

## What this is

Particle collision simulation. Loads particle positions from three simulation streams, detects collisions using spatial hashing, resolves collision responses, and generates statistics.

## Environment

- Python 3.11, working dir `/app`, source `/app/runtime/`, output `/app/runtime/output/`
- pytest available globally

## Processing stages

1. **Load** — Read particle position streams from simulation data files.
2. **Hash** — Assign particles to spatial grid cells for broad-phase detection.
3. **Detect** — Check particle pairs in nearby cells for actual collisions within the configured radius.
4. **Resolve** — Compute elastic collision impulse using standard restitution formula. Every detected pair gets a response computed — do not skip or filter any pairs.
5. **Report** — Generate collision statistics and summary metrics.

## Symptoms

Some collisions go undetected. Response velocity values are wrong. Statistics don't match expected counts.

## Expected output

- `/app/runtime/output/collisions.json`: list with `pair`(list[str]), `cell`(list[int]), `response_velocity`(float), `restitution`(float)
- `/app/runtime/output/summary.json`: `total_collisions`=123, `unique_pairs`=63, `avg_response_velocity`=1.254651, `max_response_velocity`=3.603748, `cells_with_collisions`=21

## Key files

| File | Purpose |
|------|---------|
| `/app/runtime/hasher.py` | Spatial hashing and neighbor search |
| `/app/runtime/resolver.py` | Collision response computation |
| `/app/runtime/config.ini` | Grid sizes, physics parameters |

## Task

Find and fix the bugs only. Do not add new logic or optimizations — just correct the existing code.
