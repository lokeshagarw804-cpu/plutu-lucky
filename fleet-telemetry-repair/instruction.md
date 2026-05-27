# Fleet Telemetry Aggregation — Debugging Task

## Overview

A fleet telemetry engine ingests GPS pings from delivery vehicles, segments them into trips at idle gaps, computes distance and fuel, scores drivers, and produces a report.

## Environment

- Python 3.11, stdlib only
- Runtime at `/app/runtime/`, config at `/app/runtime/config.ini`
- Vehicle data in `/app/runtime/data/` (JSON files)

## Pipeline Stages

1. **Loader** (`loader.py`) — reads vehicle JSON feeds
2. **Segmenter** (`trip_segmenter.py`) — splits pings into trips at idle gaps
3. **Distance** (`distance_calc.py`) — Haversine between consecutive pings
4. **Fuel** (`fuel_calculator.py`) — accumulates fuel usage per trip
5. **Scorer** (`scorer.py`) — weighted score from efficiency, speed compliance, idle ratio
6. **Aggregator** (`aggregator.py`) — assembles final report sorted by vehicle

## Symptoms

The engine runs without errors but output is wrong:
- Total fleet distance is lower than expected (~60 km, should be ~70.1 km)
- Some trips that should stay together at idle boundaries are split
- Fuel totals for multi-ping trips look too low
- Driver scores for vehicles missing speed-compliance data are deflated
- Report vehicle ordering puts V10 between V1 and V2

## Expected Correct Output

- 7 total trips across all vehicles
- Fleet distance: ~70.14 km
- V3 must have highest driver score (~0.87)
- Report ordering: V1, V2, V3, V10, V12

## Output Files

- `/app/runtime/output/report.json` — full fleet report
- `/app/runtime/output/summary.json` — aggregate stats

## Task

Find and fix bugs in runtime modules so output matches expected behavior. Multiple files have interacting defects.
