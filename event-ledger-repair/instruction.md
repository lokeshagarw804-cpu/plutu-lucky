# Event Ledger Replay — Debugging Task

## Overview

An event sourcing ledger replay engine ingests transaction events from multiple account streams, merges them into a globally ordered sequence, aggregates running balances into fixed-duration time windows, and runs reconciliation checks to flag accounts with sustained high-balance periods. The system handles multiple account types and produces both a ledger state summary and a reconciliation anomaly report.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, stream data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Processing Stages

1. *Stream Loading* (`/app/runtime/loader.py`) — Reads JSON event stream files from `/app/runtime/data/`, filtering by the configured active account types listed in the `[accounts]` section

2. *Event Merging* (`/app/runtime/sorter.py`) — Merges events from all loaded streams into a single globally ordered sequence. The correct deterministic ordering is by timestamp first, then stream identifier, then sequence number within the stream

3. *Window Aggregation* (`/app/runtime/aggregator.py`) — Groups events into fixed-duration time windows and tracks per-stream balance state. Each window snapshot should reflect the final balance state at window close, not cumulative totals across snapshots

4. *Reconciliation* (`/app/runtime/reconciler.py`) — Identifies streams where balance exceeds the configured threshold for consecutive windows. Production alerting parameters are defined in the strict reconciliation configuration section

5. *Report Generation* (`/app/runtime/reporter.py`) — Assembles output JSON files from aggregation and reconciliation results

## Problem

The system runs without crashing but produces incorrect results:
- Some account streams that should appear in output are missing entirely
- Final balance values for certain streams are significantly higher than expected given the transaction history
- The reconciliation report detects fewer anomalies than expected based on the configured thresholds
- Event ordering appears non-deterministic when multiple streams have events at identical timestamps

## Expected Correct Output

When all defects are resolved:
- All 5 account streams should be loaded (savings, checking, credit, merchant types)
- The system should process 84 total events across 4 time windows
- Final balances should reflect actual running totals (stream_alpha: 1900.0, stream_beta: 2275.0, stream_delta: 2845.0, stream_epsilon: 180.0, stream_gamma: 3380.0)
- Reconciliation should detect 5 anomalies including stream_epsilon flagged at medium severity

## Output Schema

### /app/runtime/output/ledger_state.json

| Field | Type | Description |
|-------|------|-------------|
| stream_count | integer | Number of streams processed |
| total_events | integer | Total events across all windows |
| window_count | integer | Number of time windows |
| final_balances | object | Map of stream_id to final balance amount |
| streams_processed | array[string] | Sorted list of stream identifiers |

### /app/runtime/output/reconciliation_report.json

| Field | Type | Description |
|-------|------|-------------|
| total_anomalies | integer | Number of detected anomalies |
| anomalies | array | List of anomaly objects |
| anomalies[].stream_id | string | Stream that triggered the anomaly |
| anomalies[].start_window | integer | First window index of anomaly |
| anomalies[].end_window | integer | Last window index of anomaly |
| anomalies[].consecutive_windows | integer | Number of consecutive flagged windows |
| anomalies[].severity | string | "high" or "medium" based on duration |
| windows_analyzed | integer | Total windows checked |
| has_high_severity | boolean | Whether any high severity anomaly exists |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Ledger parameters, account filters, reconciliation thresholds |
| /app/runtime/loader.py | Stream loading and account type filtering |
| /app/runtime/sorter.py | Multi-stream event merge and ordering |
| /app/runtime/aggregator.py | Time-window balance aggregation |
| /app/runtime/reconciler.py | Balance anomaly detection |
| /app/runtime/reporter.py | Output report generation |
| /app/runtime/run_ledger.py | Main entry point orchestrating all stages |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
