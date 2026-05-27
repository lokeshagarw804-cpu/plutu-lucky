# Fleet Telemetry Monitor — Debugging Task

## Overview

A fleet monitoring system ingests telemetry from trucks, applies sliding-window analysis to detect speed spikes, fuel consumption anomalies, and thermal deviations, scores alerts by weighted severity, and writes JSON reports.

## Environment

- Python 3.11, runtime at `/app/runtime/`
- Config: `/app/runtime/config.ini`
- Tools: uv, pytest available system-wide

## Pipeline Stages

1. **Loading** (`loader.py`) — reads per-vehicle JSON from `/app/runtime/data/`
2. **Analysis** (`analyzer.py`) — sliding window over readings; counts speed spikes, fuel drops, thermal deviation
3. **Detection** (`detector.py`) — finds consecutive anomalous windows meeting min_consecutive threshold
4. **Scoring** (`scorer.py`) — weighted severity from normalized components
5. **Reporting** (`reporter.py`) — groups alerts by vehicle, sorts, writes output

## Symptoms

- Speed spike counts don't match hand-calculated values for boundary readings
- Fuel consumption per window is lower than expected cumulative drops
- Window count per vehicle doesn't match expected from overlap config
- Severity scores appear inflated relative to component values
- Vehicle ordering doesn't follow numeric identifier sequence

## Expected Correct Output

- 7 total alerts across 4 vehicles affected
- Total duration across all alerts: 17 windows
- Total speed spikes: 54
- Max severity: 0.5834
- Vehicle order: truck_1, truck_3, truck_7, truck_12

## Output Files

- `/app/runtime/output/alerts.json` — array of alert objects
- `/app/runtime/output/summary.json` — aggregate statistics

## Your Task

Find and fix defects in the runtime source so output matches expected behavior. Multiple modules contain interacting bugs.
