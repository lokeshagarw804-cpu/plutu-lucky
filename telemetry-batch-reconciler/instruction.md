# Telemetry Batch Reconciler - Broken Pipeline

The batch reconciler in `/environment/runtime/` processes telemetry events from multiple stations, deduplicates boundary overlaps, aggregates statistics, and produces a settlement report. It's been producing inconsistent outputs since last deploy.

## Symptoms

- Some station totals show wrong event counts (events getting dropped or double-counted at batch boundaries)
- Batch B004 shows `PROCESSING` as its final state despite having a settlement record
- Retry counts look inflated for batches that went through multiple retry cycles
- Event ordering within batches is non-deterministic when timestamps collide
- Mean values have occasional precision drift compared to expected simple averages

## What to Fix

Run `python3 /environment/runtime/run_reconciler.py` to produce `/output/reconciliation_report.json`. The report must contain correct:

- `batch_summaries`: per-batch stats with proper dedup, deterministic sort by `(ts, seq)`, and accurate means
- `station_totals`: correct event counts and overall means per station
- `state_report`: correct final states (all batches should reach `SETTLED`), accurate retry counts, proper history lengths

## Key Files

- `runtime/window_dedup.py` — boundary deduplication
- `runtime/aggregator.py` — statistics computation
- `runtime/state_machine.py` — batch lifecycle transitions
- `runtime/config.ini` — pipeline configuration (defines expected behavior)
- `runtime/reconciler.py` — orchestration logic
