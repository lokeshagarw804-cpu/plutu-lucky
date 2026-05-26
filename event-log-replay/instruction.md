# Event Log Replay — Debugging Task

## What this is

Distributed system replay tool. Reads event logs from three service nodes, merges into time windows, checks causal ordering with vector clocks, and generates anomaly reports.

## Environment

- Python 3.11, working dir `/app`, source `/app/runtime/`, output `/app/runtime/output/`
- pytest available globally

## Processing stages

1. **Load** — Read JSONL logs from each node, merge events into time windows based on configured threshold.
2. **Causality** — Compare vector clocks between events in same window. Detect happens-before violations where ordering contradicts timestamps. Check drift tolerance.
3. **Reporting** — Score anomalies per source node as weighted average across targets. Apply confidence factor based on window spread. Sort descending by severity with source_node tiebreaker.

## Symptoms

Wrong number of violations reported, anomaly scores don't match expected output, some violations being missed entirely.

## Expected output

- `/app/runtime/output/anomalies.json`: list with fields `source_node`(str), `severity`(float), `violation_count`(int), `target_nodes`(list[str])
- `/app/runtime/output/summary.json`: fields `total_anomalies`, `nodes_affected`, `total_violations`, `max_severity`

## Key files

| File | Purpose |
|------|---------|
| `/app/runtime/causality.py` | Vector clock comparison and violation detection |
| `/app/runtime/reporter.py` | Severity scoring with confidence |
| `/app/runtime/loader.py` | Log loading and time windowing |
| `/app/runtime/config.ini` | Parameters and thresholds |

## Task

Find and fix the bugs. Multiple interacting defects across files — fixing one in isolation will not produce correct output.
