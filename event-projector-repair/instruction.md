# Event Projector Repair — Debugging Task

## Overview

An event-sourced CQRS projector replays domain events from multiple aggregate streams, builds materialized read-model views through periodic snapshots, handles event deduplication, and produces the final projection state. The system processes heterogeneous aggregate types (orders, inventory, customers, shipments) and produces both a materialized view and a replay sequence report.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, event data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes aggregate event streams through five stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format aggregate files from `/app/runtime/data/`, filtering to only aggregates whose type appears in the active_types config

2. *Replay Sequencing* (`/app/runtime/replayer.py`) — Merges events from all loaded aggregates into a single chronologically ordered sequence. For events sharing the same timestamp from different aggregates, ordering is deterministic using aggregate_id alphabetically then seq within that aggregate.

3. *Deduplication* (`/app/runtime/deduplicator.py`) — Removes duplicate events within a configured window of preceding positions

4. *Projection* (`/app/runtime/projector.py`) — Applies events to build read-model state, taking snapshots at the interval configured in the `projection.materialized` section. Each snapshot captures only the events processed in that specific interval — not cumulative state from previous intervals.

5. *View Assembly* (`/app/runtime/view_builder.py`) — Produces the final materialized view with per-aggregate event counts and snapshot history

## Problem

The system produces output but with several anomalies:
- Fewer events and aggregates appear than expected given the data files present
- The snapshot interval used does not match the intended production configuration
- Projection snapshots show suspiciously growing totals across intervals
- Events at the same timestamp appear in non-deterministic order across runs
- The deduplication window appears slightly wider than configured

## Expected Correct Output

When all defects are resolved:
- All 43 events from 4 aggregates (order: 13, inventory: 12, customer: 10, shipping: 8) are projected
- Snapshot interval is 10 (from projection.materialized section)
- 5 snapshots are produced (43 events / 10 per snapshot = 5)
- First snapshot contains exactly 10 events (one interval worth)
- Last snapshot contains 3 events (43 mod 10 = 3)
- Events at timestamp 1700000500 are ordered: inventory, order, order, shipping
- Active aggregates are: customer, inventory, order, shipping

## Output Schema

### /app/runtime/output/materialized_view.json

| Field | Type | Description |
|-------|------|-------------|
| total_events_projected | integer | Total events processed across all aggregates |
| aggregate_count | integer | Number of active aggregates |
| aggregates | array[string] | Sorted list of aggregate identifiers |
| per_aggregate_counts | object | Total event count per aggregate |
| snapshot_count | integer | Number of projection snapshots taken |
| snapshots | array | List of snapshot objects |
| snapshots[].snapshot_id | integer | Sequential snapshot identifier |
| snapshots[].events_processed | integer | Cumulative events at snapshot point |
| snapshots[].interval_start | integer | First event index in interval |
| snapshots[].interval_end | integer | Last event index in interval |
| snapshots[].state | object | Per-aggregate counts for this interval only |
| dedup_stats | object | Deduplication statistics |
| dedup_stats.total_input | integer | Events before dedup |
| dedup_stats.total_output | integer | Events after dedup |
| dedup_stats.duplicates_removed | integer | Removed duplicates |
| dedup_stats.window_size | integer | Configured dedup window |

### /app/runtime/output/replay_sequence.json

| Field | Type | Description |
|-------|------|-------------|
| total_events | integer | Total events in replay sequence |
| replay_order | array | Ordered event records |
| replay_order[].event_id | string | Event identifier |
| replay_order[].aggregate_id | string | Source aggregate |
| replay_order[].timestamp | integer | Event timestamp |
| replay_order[].seq | integer | Sequence within aggregate |
| snapshot_interval | integer | Configured snapshot interval |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Projection parameters and aggregate configuration |
| /app/runtime/loader.py | Aggregate stream loading with type filtering |
| /app/runtime/replayer.py | Chronological event replay sequencing |
| /app/runtime/deduplicator.py | Event deduplication within window |
| /app/runtime/projector.py | Snapshot-based projection state building |
| /app/runtime/view_builder.py | Final materialized view assembly |
| /app/runtime/run_projector.py | Main entry point and orchestration |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
