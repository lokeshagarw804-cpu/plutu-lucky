# Event Replay Engine Repair — Debugging Task

## Overview

A CQRS event replay engine processes domain events from multiple command streams (orders, payments, adjustments, refunds), sequences them into a deterministic global order, projects materialized account balances, captures periodic balance snapshots, and reconciles the final state against those checkpoints for audit verification.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, event data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Processing Stages

1. *Stream Loading* (`/app/runtime/stream_loader.py`) — Reads JSON event files from `/app/runtime/data/` for each configured stream. Only streams listed in the `included_streams` configuration value are loaded.

2. *Sequencing* (`/app/runtime/sequencer.py`) — Merges events from all loaded streams into a single deterministic sequence. The correct global ordering is by timestamp first, then by stream_id (alphabetical), then by sequence_num within a stream. This ensures reproducible replay across runs.

3. *Projection* (`/app/runtime/projector.py`) — Applies each sequenced event to build materialized account balances. Credits add to the balance, debits subtract from it.

4. *Snapshot Building* (`/app/runtime/snapshot_builder.py`) — Captures point-in-time balance checkpoints at regular intervals (every N events as configured). Each snapshot records the current balance for each account at that moment.

5. *Reconciliation* (`/app/runtime/reconciler.py`) — Compares the final projected balances against the last snapshot checkpoint. Uses the precision configured under `[projection.reconciliation]` for rounding both sides before comparison.

## Problem

The system produces output but with several anomalies:
- The total number of processed events appears lower than expected given the number of source streams
- Reconciliation reports discrepancies between final projected state and the last snapshot
- Snapshot balances grow unexpectedly large across successive checkpoints
- Some account balance orderings in output appear non-deterministic across repeated runs

## Expected Correct Output

When all defects are resolved:
- All 4 streams should be loaded (orders, payments, adjustments, refunds) producing 48 total events
- The sequencer should produce a stable deterministic ordering across runs
- Snapshots should reflect the exact account balances at each checkpoint moment
- Reconciliation should report status "clean" with zero discrepancies

## Output Schema

### /app/runtime/output/projection_state.json

| Field | Type | Description |
|-------|------|-------------|
| total_events_processed | integer | Total number of events replayed |
| total_accounts | integer | Number of unique accounts |
| balances | object | Map of account_id to final balance (float) |
| streams_loaded | array[string] | List of stream identifiers that were loaded |

### /app/runtime/output/snapshots.json

| Field | Type | Description |
|-------|------|-------------|
| interval_events | integer | Events between snapshots |
| total_snapshots | integer | Number of checkpoints captured |
| snapshots | array | List of snapshot checkpoint objects |
| snapshots[].checkpoint_index | integer | Zero-based snapshot number |
| snapshots[].event_count | integer | Cumulative events processed at this point |
| snapshots[].balances | object | Map of account_id to balance at checkpoint |

### /app/runtime/output/reconciliation.json

| Field | Type | Description |
|-------|------|-------------|
| total_accounts | integer | Number of accounts checked |
| reconciled_accounts | integer | Accounts matching within tolerance |
| discrepancies | array | List of mismatch objects |
| discrepancies[].account_id | string | Account with mismatch |
| discrepancies[].projected_balance | float | Balance from projection |
| discrepancies[].snapshot_balance | float | Balance from last snapshot |
| discrepancies[].difference | float | Absolute difference |
| status | string | "clean" or "discrepancies_found" |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Stream selection, projection settings, snapshot intervals |
| /app/runtime/stream_loader.py | Loads events from configured command streams |
| /app/runtime/sequencer.py | Establishes deterministic global event ordering |
| /app/runtime/projector.py | Builds materialized account balances from events |
| /app/runtime/snapshot_builder.py | Captures periodic balance checkpoints |
| /app/runtime/reconciler.py | Audits final state against snapshot history |
| /app/runtime/run_replay.py | Main entry point orchestrating all stages |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
