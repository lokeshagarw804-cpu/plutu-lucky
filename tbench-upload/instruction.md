# Geofence Alert Engine — Debugging Task

## Overview

Fleet monitoring tool: reads GPS pings from three vehicle feeds, checks geofence zone violations via ray-casting, tracks dwell time with a state machine, and outputs severity-ranked alerts.

## Environment

- Python 3.11, working dir `/app`, source at `/app/runtime/`, output at `/app/runtime/output/`
- pytest available globally

## How it works

1. **Load** — Reads JSONL fleet feeds, groups readings in time windows (inclusive boundary, `<=` configured seconds).
2. **Geofence** — Ray-casting point-in-polygon. Points on horizontal edges count as inside.
3. **Dwell** — State machine: OUTSIDE→ENTERING→INSIDE→EXITING. Two consecutive inside-readings confirm entry. Counter resets only on transition back to OUTSIDE.
4. **Alerts** — Severity per vehicle = weighted average of dwell scores, but only across zones that vehicle actually violated (the divisor is the sum of those zones' weights, not all configured weights). Sort: `(zone_id, -severity, vehicle_id)`.

## Symptoms

Vehicles never reach INSIDE state, boundary points misclassified, severity exceeds 1.0 (weight divisor seems wrong), non-deterministic ordering.

## Expected output

- `/app/runtime/output/alerts.json`: 9 alerts, schema: `zone_id`(str), `vehicle_id`(str), `severity`(float), `dwell_seconds`(int), `readings_inside`(int)
- `/app/runtime/output/summary.json`: `total_alerts`=9, `zones_violated`=3, `total_dwell`=1765, `max_severity`≈0.7769

## Key files

| File | Purpose |
|------|---------|
| `/app/runtime/geofence.py` | Point-in-polygon tests |
| `/app/runtime/tracker.py` | Dwell state machine |
| `/app/runtime/alerts.py` | Severity + sorting |
| `/app/runtime/loader.py` | Feed loading + time windows |
| `/app/runtime/config.ini` | Zone defs, weights, thresholds |

## Task

Fix the bugs in the runtime source. Multiple defects across files — they interact.
