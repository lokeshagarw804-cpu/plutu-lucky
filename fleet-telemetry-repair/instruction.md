# Fleet Telemetry Anomaly Detection — Debugging Task

## Overview

A fleet telemetry pipeline ingests vehicle sensor streams, computes rolling anomaly scores via EWMA, groups scores into time windows, fuses multi-sensor data with configured weights, classifies severity, and writes a report.

## Environment

- Python 3.11, stdlib only
- Runtime: `/app/runtime/`
- Entry: `python3 -m runtime.main`
- Tools: `uv`, `pytest`

## Pipeline Stages

1. **Loader** (`loader.py`) — reads JSONL sensor feeds from `/app/runtime/data/`
2. **Scorer** (`scorer.py`) — EWMA-based Z-score computation per sensor
3. **Aggregator** (`aggregator.py`) — groups scored readings into fixed time windows
4. **Fusion** (`fusion.py`) — weighted combination of per-sensor window peaks
5. **Classifier** (`classifier.py`) — maps fused scores to severity tiers
6. **Reporter** (`reporter.py`) — writes `anomalies.json` and `summary.json`

## Symptoms

The pipeline runs without errors but produces incorrect output:
- Zero anomalies detected despite data containing obvious spikes
- EWMA statistics appear to drift incorrectly over time
- Window boundaries don't align with the documented interval semantics
- Severity classification doesn't produce the expected tier distribution
- Fused scores seem lower than expected given configured sensor weights

## Expected Correct Output

When fixed, `summary.json` should report:
- `total_anomalies`: 11
- `vehicles_affected`: 4
- `severity_counts`: warning=5, critical=2, emergency=4
- `max_fused_score` ≈ 59.01

## Output Files

- `/app/runtime/output/anomalies.json` — list of anomaly objects with `vehicle_id`, `window_start`, `window_end`, `fused_score`, `severity`, `sensors_reporting`
- `/app/runtime/output/summary.json` — aggregate stats with `total_anomalies`, `vehicles_affected`, `severity_counts`, `max_fused_score`, `avg_fused_score`, `fleet_size`

## Task

Find and fix the defects in the runtime modules so the pipeline produces correct output.
