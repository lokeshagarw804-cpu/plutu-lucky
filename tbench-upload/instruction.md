# Geofence Alert Engine — Debugging Task

## What this is

Fleet monitoring tool. Reads GPS pings from three vehicle feeds, checks geofence zone violations, tracks dwell time, and outputs severity-ranked alerts.

## Environment

- Python 3.11, working dir `/app`, source at `/app/runtime/`, output at `/app/runtime/output/`
- pytest available globally

## Processing stages

1. **Load** — Reads JSONL fleet feeds, merges into time-ordered sequence.
2. **Geofence** — Tests each reading against polygon zones using ray-casting algorithm.
3. **Dwell** — State machine tracks how long vehicles stay inside zones.
4. **Alerts** — Computes severity scores per vehicle across violated zones. Produces sorted alert list.

## Symptoms

System runs but output is wrong. Very few or no alerts generated. Some expected zone entries are missed entirely.

## Expected output

- `/app/runtime/output/alerts.json`: list with `zone_id`(str), `vehicle_id`(str), `severity`(float), `dwell_seconds`(int), `readings_inside`(int)
- `/app/runtime/output/summary.json`: `total_alerts`=9, `zones_violated`=3, `total_dwell`=1765, `max_severity`≈0.7769

## Key files

| File | Purpose |
|------|---------|
| `/app/runtime/geofence.py` | Point-in-polygon boundary tests |
| `/app/runtime/tracker.py` | Dwell state machine |
| `/app/runtime/alerts.py` | Severity computation and output |
| `/app/runtime/config.ini` | Zone definitions, weights |

## Task

Find and fix the bugs. Multiple interacting defects across several files.
