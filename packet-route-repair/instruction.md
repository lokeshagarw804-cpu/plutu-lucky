# Packet Route Repair — Debugging Task

## What this is

Network flow analyzer. Reads packet logs from three router nodes, computes shortest-path costs via Dijkstra, detects routing anomalies (loops and suboptimal paths), and produces flow quality reports.

## Environment

- Python 3.11, working dir `/app`, source `/app/runtime/`, output `/app/runtime/output/`
- pytest available globally

## Processing stages

1. **Ingest** — Load JSONL packet logs from each router node.
2. **Route** — Compute optimal path costs between all node pairs using Dijkstra.
3. **Track** — Detect routing loops by tracking visited nodes across the full packet path. A loop exists when any node has already been visited earlier in that packet's traversal.
4. **Report** — Score anomalies per source-destination pair. Flow cost normalization divides by total accumulated path costs for that source (not just the last destination's cost). Sort globally by descending score with source and destination as tiebreakers.

## Symptoms

Some routing loops go undetected even though packets clearly revisit nodes through indirect paths. Suboptimal path detection misses cases where the indirect route is only slightly cheaper than direct. Flow scores and ordering seem wrong.

## Expected output

- `/app/runtime/output/flows.json`: list with `source_node`, `dest_node`, `anomaly_score`, `path_cost`, `optimal_cost`, `has_loop`
- `/app/runtime/output/summary.json`: `total_flows`, `loops_detected`, `suboptimal_count`, `max_anomaly_score`, `avg_anomaly_score`

## Key files

| File | Purpose |
|------|---------|
| `router.py` | Dijkstra shortest-path |
| `tracker.py` | Loop detection |
| `reporter.py` | Anomaly scoring and reports |
| `config.ini` | Network parameters |

## Task

Find and fix the bugs. Multiple interacting defects.
