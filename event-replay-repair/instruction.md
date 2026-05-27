# Event Replay Engine — Debugging Task

## Overview

An event replay engine ingests timestamped domain events from multiple source streams, merges them into a globally ordered sequence, projects payload fields according to configuration, and builds per-entity aggregate state snapshots. The system is used for rebuilding read-model state from an append-only event store.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, event data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Processing Stages

1. *Stream Loading* (`/app/runtime/loader.py`) — Reads JSON event files from `/app/runtime/data/` for each stream listed in the configuration. Stream names are parsed from a comma-separated list in the config.

2. *Event Sequencing* (`/app/runtime/sequencer.py`) — Merges events from all loaded streams and sorts them into a deterministic global order. The correct replay order is by timestamp, then stream identifier, then sequence number. Events are then split into fixed-size batches for incremental processing. The production batch size is defined under the `replay.incremental` configuration section.

3. *Payload Projection* (`/app/runtime/projector.py`) — Filters each event payload to retain only the fields specified in the projection configuration. Non-matching fields are discarded before aggregation.

4. *Entity Aggregation* (`/app/runtime/aggregator.py`) — Builds per-entity state from the projected event stream. Gauge-type fields (like monetary amounts and status values) use last-write-wins semantics — only the most recent value is kept. Counter-type fields accumulate across events.

5. *Snapshot Output* (`/app/runtime/snapshot_writer.py`) — Serializes the aggregate state and replay metadata to JSON output files.

## Problem

The system runs without errors but produces incorrect aggregate state:
- Some entities have inflated numeric field values that don't match expected totals
- A source stream that should contribute events appears to be silently skipped
- The batch count in output metadata doesn't match what the incremental replay configuration implies
- Certain entity field values are non-deterministic across runs when events from different streams share the same timestamp

## Expected Correct Output

When all defects are resolved:
- All 4 configured streams should be loaded (stream_orders, stream_payments, stream_inventory, stream_fulfillment) producing 57 total events
- Events should be processed in 3 batches of 25-25-7
- Entity `ent_101` should have `order_total` of 175.00 (the latest confirmed order value, not an accumulation of all order events)
- Entity `ent_101` should have `payment_amount` of -50.00 (the most recent payment event is the refund)
- Entities with fulfillment stream events should show `fulfillment_status` of "dispatched"
- The replay summary should report batch_size of 25

## Output Schema

### /app/runtime/output/entity_snapshot.json

| Field | Type | Description |
|-------|------|-------------|
| version | string | Version prefix from config |
| total_entities | integer | Number of distinct entities |
| entities | array | List of entity state objects |
| entities[].entity_id | string | Unique entity identifier |
| entities[].event_count | integer | Total events processed for entity |
| entities[].last_updated | integer | Timestamp of last event applied |
| entities[].fields | object | Projected field values |

### /app/runtime/output/replay_summary.json

| Field | Type | Description |
|-------|------|-------------|
| total_events_processed | integer | Total events across all streams |
| total_streams | integer | Number of streams loaded |
| batch_count | integer | Number of processing batches |
| batch_size | integer | Events per batch |
| entity_count | integer | Distinct entities in snapshot |
| streams_loaded | array[string] | Sorted list of loaded stream names |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Stream list, replay parameters, projection fields |
| /app/runtime/loader.py | Reads and parses event stream JSON files |
| /app/runtime/sequencer.py | Merges and orders events, splits into batches |
| /app/runtime/projector.py | Filters payload fields per projection config |
| /app/runtime/aggregator.py | Builds per-entity state with gauge/counter semantics |
| /app/runtime/snapshot_writer.py | Writes output JSON files |
| /app/runtime/run_replay.py | Main orchestration entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct aggregate state matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
