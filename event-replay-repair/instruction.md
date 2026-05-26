# Event Replay Projection — Debugging Task

## Overview

An event sourcing system replays event streams from multiple source channels (orders, payments, inventory), builds materialized projections of entity state, and generates aggregate reports. The system processes events in time-based batch windows and produces deterministic output for downstream consumers. Currently the outputs contain several inconsistencies.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source, config, data, output)
- *Global system-wide tooling*: uv and pytest are available

## Processing Stages

1. *Loading* — Reads event records from stream JSON files in /app/runtime/data/. Each file represents a distinct event source (orders, payments, inventory) with its own local sequence numbering.

2. *Filtering* — Events are filtered against the configured allowed type list from the streams section of /app/runtime/config.ini. Only events with registered types proceed to replay.

3. *Sorting* — Events are sorted into deterministic replay order. For events sharing the same timestamp from different streams, the correct canonical order is (timestamp, stream_id, sequence) since sequence numbers are local to each individual stream.

4. *Projection Building* — Sorted events are replayed in time-based batch windows. The streaming replay mode (section replay.streaming in /app/runtime/config.ini) uses a 24-hour window for incremental projection builds. Entity state is tracked across windows. Batch totals are computed per-window and the final snapshot reflects only the most recent window (snapshot_mode=latest).

5. *Reporting* — Two output files are produced: an event processing log with the replay sequence, and a summary report with batch statistics, entity states, and per-stream totals from the final batch window.

## Problem

The system runs without errors but produces output that does not match specifications:
- Certain inventory events of a known type are silently dropped from processing
- The batch window size appears larger than intended, producing fewer batches than expected
- Aggregate totals in the final report reflect cumulative values across all windows instead of only the latest window
- Event ordering is non-deterministic when multiple streams have events at the same timestamp

## Expected Correct Output

When fixed, the system should produce:
- All 43 events from 3 streams are included (none dropped by the filter)
- Events are split into 4 batch windows using the 24-hour streaming window
- Batch totals reflect only the final (most recent) window, not accumulated across all windows
- Events with the same timestamp are deterministically ordered by (timestamp, stream_id, sequence)

## Output Schema

### /app/runtime/output/event_log.json

| Field | Type | Description |
|-------|------|-------------|
| total_events | int | Total number of events processed after filtering |
| entries | list | Ordered list of processed event entries |
| entries[].position | int | Zero-based position in replay order |
| entries[].event_id | string | Unique event identifier |
| entries[].stream_id | string | Source stream identifier |
| entries[].sequence | int | Sequence number (local to stream) |
| entries[].timestamp | string | ISO 8601 timestamp |
| entries[].event_type | string | Type of event |
| entries[].entity_id | string | Entity this event affects |
| entries[].payload_keys | list | Sorted list of payload field names |

### /app/runtime/output/replay_summary.json

| Field | Type | Description |
|-------|------|-------------|
| total_events_processed | int | Total events that passed filtering |
| total_batches | int | Number of batch windows created |
| stream_counts | object | Event count per stream_id |
| type_counts | object | Event count per event_type |
| total_entities | int | Number of distinct entities tracked |
| entity_states | object | Final state snapshot per entity |
| entity_states[].entity_id | string | Entity identifier |
| entity_states[].stream_id | string | Source stream for this entity |
| entity_states[].event_count | int | Number of events for this entity |
| entity_states[].last_event_type | string | Most recent event type |
| entity_states[].last_timestamp | string | Timestamp of most recent event |
| entity_states[].total_amount | float | Cumulative amount from payloads |
| batch_totals | object | Per-stream totals from the final batch window only |
| batch_totals[].event_count | int | Events in the final batch for this stream |
| batch_totals[].total_amount | float | Amount total in the final batch for this stream |
| batch_totals[].entity_count | int | Distinct entities in the final batch for this stream |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/run_replay.py | Main entry point, orchestrates all stages |
| /app/runtime/loader.py | Reads events from stream JSON files |
| /app/runtime/filter.py | Filters events by configured allowed types |
| /app/runtime/sorter.py | Sorts events into deterministic replay order |
| /app/runtime/projector.py | Batch windowing and projection building |
| /app/runtime/reporter.py | Output report generation |
| /app/runtime/config.ini | Configuration for streams, replay, and output |
| /app/runtime/data/orders_stream.json | Order lifecycle events (17 records) |
| /app/runtime/data/payments_stream.json | Payment processing events (13 records) |
| /app/runtime/data/inventory_stream.json | Stock management events (13 records) |

## Your Task

Identify and fix the defects in the runtime source files under /app/runtime/ that cause incorrect event filtering, oversized batch windows, accumulated totals instead of per-window snapshots, and non-deterministic event ordering.
