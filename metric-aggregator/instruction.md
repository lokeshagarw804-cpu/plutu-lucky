# Metric Aggregator Repair — Debugging Task

## Overview

A distributed metrics aggregation engine collects performance data from multiple service nodes, applies windowed aggregation, computes degradation rankings via weighted percentile scoring, and detects sustained performance degradation incidents. The system processes latency, error rate, and throughput metrics to produce a health assessment report.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, metric data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes service metrics through six stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format metric files from `/app/runtime/data/`

2. *Filtering* (`/app/runtime/filter.py`) — Aligns time ranges across nodes with different recording start times by trimming to shared overlap

3. *Aggregation* (`/app/runtime/aggregator.py`) — Applies sliding window with configurable step to compute per-window statistics (mean, max, p90) for each metric

4. *Ranking* (`/app/runtime/ranker.py`) — Computes weighted degradation scores combining normalized latency, error rate, and inverse throughput, then assigns percentile ranks within each window

5. *Detection* (`/app/runtime/detector.py`) — Identifies consecutive windows where degradation percentile exceeds a threshold, flagging sustained incidents

6. *Reporting* (`/app/runtime/reporter.py`) — Generates structured health report with per-node summaries and incident details

## Problem

The system produces output but with several anomalies:
- Fewer degradation incidents detected than expected for the given data patterns
- Some nodes that clearly show degrading performance are not flagged
- The number of aggregation windows appears inconsistent with configured parameters
- Degradation scores don't reflect the expected contribution of all metric weights

## Expected Correct Output

When all defects are resolved:
- The system should detect exactly 3 degradation incidents
- 3 nodes should be affected: service_api, service_worker, and service_gateway
- service_api should show the worst degradation with severity 1.0 across 8 windows
- service_worker should show a shorter incident of 3 windows
- service_gateway should show an incident of 5 windows with severity ~0.82
- service_cache should have no incidents (best performer)
- All 4 nodes must appear in the ranking and node details

## Output Schema

### /app/runtime/output/health_report.json

| Field | Type | Description |
|-------|------|-------------|
| summary.total_incidents | integer | Number of detected incidents |
| summary.nodes_affected | integer | Number of unique nodes with incidents |
| summary.max_severity | float | Highest severity score across incidents |
| summary.total_degraded_windows | integer | Sum of all incident durations |
| summary.worst_node | string | Node with highest average percentile |
| node_details | array | Per-node health summaries sorted worst-first |
| node_details[].node_id | string | Service node identifier |
| node_details[].avg_percentile | float | Mean percentile rank across windows |
| node_details[].max_percentile | float | Peak percentile rank |
| node_details[].total_incidents | integer | Incidents for this node |
| node_details[].total_degraded_windows | integer | Total degraded windows for node |
| incidents | array | List of detected degradation incidents |
| incidents[].node_id | string | Affected service node |
| incidents[].start_window | integer | First window of incident |
| incidents[].end_window | integer | Last window of incident |
| incidents[].duration_windows | integer | Incident length in windows |
| incidents[].peak_score | float | Highest percentile during incident |
| incidents[].severity | float | Computed severity score |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Aggregation parameters and node configuration |
| /app/runtime/loader.py | Metric data loading |
| /app/runtime/filter.py | Time range alignment |
| /app/runtime/aggregator.py | Windowed metric aggregation |
| /app/runtime/ranker.py | Degradation scoring and percentile ranking |
| /app/runtime/detector.py | Incident detection |
| /app/runtime/reporter.py | Health report generation |
| /app/runtime/main.py | Main entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
