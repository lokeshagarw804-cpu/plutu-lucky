# Event Ledger Replay — Debugging Task

## Overview

An event sourcing replay engine ingests transaction events from account streams, produces a globally ordered event sequence, aggregates running balances into time windows, and performs reconciliation analysis to flag anomalous account behavior. The system processes multiple account types from JSON data files and generates two output reports.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, stream data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes event data through six stages:

1. *Stream Loading* (`/app/runtime/loader.py`) — Reads JSON event stream files from `/app/runtime/data/`, filtering by account types

2. *Event Merging* (`/app/runtime/sorter.py`) — Combines events from all streams into a single ordered sequence for replay

3. *Validation* (`/app/runtime/validator.py`) — Deduplicates events and validates structure

4. *Window Aggregation* (`/app/runtime/aggregator.py`) — Groups events into fixed-duration windows and tracks per-stream balance state through batch processing

5. *Reconciliation* (`/app/runtime/reconciler.py`) — Detects streams with sustained high-balance positions across consecutive windows

6. *Report Generation* (`/app/runtime/reporter.py`) — Writes output JSON files

## Problem

The system runs without errors but produces incorrect results in several areas:
- The number of streams appearing in output does not match what the data directory contains
- Balance computations produce values that are inconsistent with the raw transaction amounts
- The reconciliation detection is less sensitive than the production configuration intends
- Event ordering may be unstable when multiple streams produce events at the same wall-clock time

## Expected Correct Output

When all defects are resolved:
- All account streams present in `/app/runtime/data/` that match configured types should be processed
- Window balances should accurately reflect the running account state after each event
- Reconciliation should use production-grade sensitivity parameters
- The total event count and stream count in the ledger state must match the actual processed data

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
| anomalies[].severity | string | Severity classification |
| windows_analyzed | integer | Total windows checked |
| has_high_severity | boolean | Whether any high severity anomaly exists |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | System parameters and threshold configuration |
| /app/runtime/loader.py | Stream loading with account type filtering |
| /app/runtime/sorter.py | Multi-stream event merge and ordering |
| /app/runtime/validator.py | Event deduplication |
| /app/runtime/aggregator.py | Time-window balance aggregation |
| /app/runtime/reconciler.py | Balance anomaly detection |
| /app/runtime/reporter.py | Output report generation |
| /app/runtime/run_ledger.py | Main entry point |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the system produces correct output. Multiple modules contain defects that interact with each other — the correct output requires all issues to be resolved together.
