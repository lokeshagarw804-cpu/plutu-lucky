# Event Log Replay — Debugging Task

## What this is

Distributed system replay tool. Reads event logs from three service nodes, merges into time windows, detects causal ordering violations using vector clocks, and generates anomaly reports.

## Environment

- Python 3.11, working dir `/app`, source `/app/runtime/`, output `/app/runtime/output/`
- pytest available globally

## Processing stages

1. **Load** — Read JSONL logs, merge events within configured time window from group start.
2. **Causality** — Compare vector clocks between events in same window. Detect happens-before violations where causal ordering contradicts timestamp ordering.
3. **Reporting** — Score anomalies per source node using weighted averages across target nodes. Sort by descending severity with source_node tiebreaker.

## Symptoms

Wrong number of violations detected, anomalies attributed to incorrect nodes, severity scores seem off.

## Expected output

- `/app/runtime/output/anomalies.json`: list with fields `source_node`(str), `severity`(float), `violation_count`(int), `target_nodes`(list[str])
- `/app/runtime/output/summary.json`: `total_anomalies`=1, `nodes_affected`=1, `total_violations`=4, `max_severity`=0.775

## Key files

| File | Purpose |
|------|---------|
| `/app/runtime/causality.py` | Vector clock comparison logic |
| `/app/runtime/reporter.py` | Severity scoring and output |
| `/app/runtime/loader.py` | Log loading and time windowing |

## Task

Find and fix the bugs in the runtime source files. There are multiple interacting defects.
