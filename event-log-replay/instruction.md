# Event Log Replay — Debugging Task

## What this is

Distributed system replay tool. Reads event logs from three service nodes, merges into time windows, checks causal ordering with vector clocks, and flags ordering anomalies.

## Environment

- Python 3.11, working dir `/app`, source `/app/runtime/`, output `/app/runtime/output/`
- pytest available globally

## How it should work

1. **Load** — Read JSONL logs, merge events within configured window (inclusive boundary — `<=`).
2. **Causality** — Compare vector clocks between events in same window. If clock B dominates clock A (B[i]>=A[i] for all i, strict > for some), then A happened-before B. Events where neither dominates are *concurrent* — not violations. A violation: B's clock shows B happened-before A, but B has later timestamp.
3. **Reporting** — Per source node with violations, compute severity as weighted average across target nodes. Weight divisor accumulates across all targets (not just the last). Sort by `(-severity, source_node)`.

## Symptoms

Too many violations flagged, concurrent events wrongly treated as causal, severity over 1.0, wrong source nodes in output.

## Expected output

- `/app/runtime/output/anomalies.json`: fields `source_node`(str), `severity`(float), `violation_count`(int), `target_nodes`(list[str])
- `/app/runtime/output/summary.json`: `total_anomalies`=1, `nodes_affected`=1, `total_violations`=4, `max_severity`=0.775

## Key files

| File | Purpose |
|------|---------|
| `/app/runtime/causality.py` | Vector clock comparison |
| `/app/runtime/reporter.py` | Severity scoring |
| `/app/runtime/loader.py` | Log merging |

## Task

Find and fix the bugs so correct anomalies are reported.
