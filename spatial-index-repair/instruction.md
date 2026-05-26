# Signal Correlator Repair — Debugging Task

## Overview

A signal correlation engine processes time-series sensor readings from multiple monitoring stations, computes pairwise windowed cross-correlations, assembles a correlation matrix, and detects significant sustained correlation events. The system handles stations with varying start times and produces both a correlation matrix and an event detection report.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, sensor data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes sensor data through six stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format station files from `/app/runtime/data/`

2. *Normalization* (`/app/runtime/normalizer.py`) — Applies z-score standardization to each station's full signal

3. *Alignment* (`/app/runtime/aligner.py`) — Computes time-overlap regions for station pairs with different recording start times

4. *Correlation* (`/app/runtime/correlator.py`) — Applies sliding window with configurable overlap to compute per-window correlation coefficients between aligned signal pairs

5. *Matrix Assembly* (`/app/runtime/matrix_builder.py`) — Builds symmetric correlation matrix from mean per-pair correlations

6. *Event Detection* (`/app/runtime/event_detector.py`) — Identifies sustained windows where correlation strength exceeds the configured threshold

## Problem

The system produces output but with several anomalies:
- Some correlation values differ from expected reference values for known test signals
- The correlation matrix station ordering does not match expected numeric identifier ordering
- Known strongly anti-correlated station pairs are not reported as events despite exceeding the correlation strength threshold
- Window counts for some pairs appear inconsistent with the configured overlap parameters
- Alignment of stations with non-aligned start times shows small numerical deviations

## Expected Correct Output

When all defects are resolved:
- The correlation matrix should order stations numerically: station_1, station_2, station_3, station_4, station_10
- Stations 1 and 2 should show strong positive correlation (>0.9)
- Stations 3 and 4 should show strong negative correlation (<-0.9)
- The system should detect 2 significant events: one positive (stations 1-2) and one negative (stations 3-4)

## Output Schema

### /app/runtime/output/correlation_matrix.json

| Field | Type | Description |
|-------|------|-------------|
| station_order | array[string] | Ordered list of station identifiers |
| matrix | array[array[float]] | Symmetric correlation matrix |
| size | integer | Number of stations |

### /app/runtime/output/detected_events.json

| Field | Type | Description |
|-------|------|-------------|
| threshold | float | Correlation threshold used |
| min_duration_windows | integer | Minimum consecutive windows |
| total_events | integer | Number of detected events |
| events | array | List of detected event objects |
| events[].station_a | string | First station in pair |
| events[].station_b | string | Second station in pair |
| events[].start_window | integer | First window index of event |
| events[].end_window | integer | Last window index of event |
| events[].duration_windows | integer | Event length in windows |
| events[].type | string | "positive" or "negative" |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Correlation parameters and station configuration |
| /app/runtime/loader.py | Station data loading |
| /app/runtime/normalizer.py | Signal z-score standardization |
| /app/runtime/aligner.py | Pairwise time alignment |
| /app/runtime/correlator.py | Windowed correlation computation |
| /app/runtime/matrix_builder.py | Correlation matrix assembly |
| /app/runtime/event_detector.py | Significant event detection |
| /app/runtime/run_spatial.py | Main entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
