A fleet telemetry system processes GPS readings from three vehicle sources, evaluates geofence boundary violations using ray-casting point-in-polygon tests, tracks dwell durations via a state machine, and generates severity-ranked alert reports.

## Environment

- Language: Python 3.11
- Working directory: `/app`
- Runtime source: `/app/runtime/`
- Data files: `/app/runtime/data/` (three JSONL fleet feeds)
- Config: `/app/runtime/config.ini`
- Output: `/app/runtime/output/`

## Processing

1. Load GPS readings from fleet feeds, merge by timestamp within a configurable time window (inclusive of boundary).
2. For each reading, test containment against polygon geofences using ray-casting. The algorithm must handle points lying exactly on horizontal polygon edges as "inside."
3. Track per-vehicle geofence state transitions (OUTSIDE/ENTERING/INSIDE/EXITING). Transition to INSIDE requires two consecutive interior readings; the confirmation counter resets only on state change back to OUTSIDE.
4. Compute alert severity as a weighted sum across all geofence zones. Zone weights accumulate globally across zones for the final divisor.
5. Output alerts sorted by `(zone_id, -severity, vehicle_id)` for deterministic ordering.

## Problem

The system produces incorrect alerts: some boundary points are misclassified, dwell tracking miscounts confirmations, time-window grouping excludes valid readings, severity normalization resets per zone, and output ordering is non-deterministic.

## Output

- `/app/runtime/output/alerts.json`: fields `zone_id` (str), `vehicle_id` (str), `severity` (float), `dwell_seconds` (int), `readings_inside` (int)
- `/app/runtime/output/summary.json`: fields `total_alerts` (int), `zones_violated` (int), `total_dwell` (int), `max_severity` (float)

## Task

Fix defects in the runtime source to produce correct output.
