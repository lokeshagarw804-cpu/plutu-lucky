# Pipeline Pressure Monitor — Debugging Task

## Overview

A pipeline pressure monitoring system processes time-series sensor readings from multiple pipeline segments, computes pressure gradients using finite differences, aggregates gradient statistics in rolling windows, and detects anomalous pressure events (surges and leaks). The system handles segments with varying start times and sensor counts, producing both a summary report and detailed event detection output.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, sensor data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes pressure data through six stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format segment files from `/app/runtime/data/`

2. *Segment Mapping* (`/app/runtime/segment_mapper.py`) — Averages multi-sensor readings per segment and maps segment metadata including physical lengths

3. *Interpolation* (`/app/runtime/interpolator.py`) — Upsamples pressure readings using cubic spline interpolation with configurable boundary conditions

4. *Gradient Calculation* (`/app/runtime/gradient_calculator.py`) — Computes temporal pressure gradients (dP/dt) using central finite difference

5. *Rolling Aggregation* (`/app/runtime/aggregator.py`) — Applies sliding windows to compute mean magnitude, peak values, and variance of gradients

6. *Threshold Detection* (`/app/runtime/threshold_engine.py`) — Identifies sustained periods where gradient magnitude exceeds the configured threshold, classifying events as surges or leaks

## Problem

The system produces output but with several anomalies:
- Gradient magnitudes are implausibly small for segments with strong pressure trends because the gradient denominator uses incorrect values
- The rolling window aggregator misses the final sample in each window, leading to slightly skewed statistics
- Leak events (sustained negative pressure drops) are not detected despite clearly decreasing pressure in some segments
- All detected events are classified as "surge" even when the gradient direction is predominantly negative
- The interpolation uses natural boundary conditions instead of the configured clamped boundary, causing end-of-segment artifacts

## Expected Correct Output

When all defects are resolved:
- The summary should order segments numerically: seg_1, seg_2, seg_3, seg_4, seg_10
- Total detected events should be 4 (2 surges, 2 leaks)
- seg_1 and seg_10 should produce surge events (strong positive pressure gradient)
- seg_3 should produce a leak event (strong negative pressure gradient)
- seg_4 should produce no events (oscillating pressure below threshold)
- seg_2 should produce no events (low-magnitude fluctuation)
- The maximum gradient magnitude across all segments should come from seg_3

## Output Schema

### /app/runtime/output/summary.json

| Field | Type | Description |
|-------|------|-------------|
| segment_order | array[string] | Ordered list of segment identifiers |
| total_segments | integer | Number of active segments |
| total_events | integer | Total detected anomalous events |
| events_by_type | object | Counts of surge and leak events |
| per_segment_windows | object | Window counts per segment |

### /app/runtime/output/events.json

| Field | Type | Description |
|-------|------|-------------|
| threshold | float | Gradient threshold used |
| min_duration_samples | integer | Minimum consecutive windows for event |
| total_events | integer | Number of detected events |
| events | array | List of detected event objects |
| events[].segment_id | string | Segment where event occurred |
| events[].start_window | integer | First window index of event |
| events[].end_window | integer | Last window index of event |
| events[].duration_windows | integer | Event length in windows |
| events[].type | string | "surge" or "leak" |
| events[].peak_magnitude | float | Maximum gradient magnitude in event |

### /app/runtime/output/gradient_stats.json

| Field | Type | Description |
|-------|------|-------------|
| [segment_id].num_gradient_samples | integer | Number of gradient values |
| [segment_id].max_magnitude | float | Maximum absolute gradient |
| [segment_id].mean_magnitude | float | Mean absolute gradient |
| [segment_id].total_windows | integer | Windows computed for segment |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Pipeline parameters and segment configuration |
| /app/runtime/loader.py | Segment data loading |
| /app/runtime/segment_mapper.py | Sensor-to-segment mapping and averaging |
| /app/runtime/interpolator.py | Cubic spline upsampling |
| /app/runtime/gradient_calculator.py | Temporal gradient computation |
| /app/runtime/aggregator.py | Rolling window statistics |
| /app/runtime/threshold_engine.py | Anomalous event detection and classification |
| /app/runtime/run_pipeline.py | Main entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
