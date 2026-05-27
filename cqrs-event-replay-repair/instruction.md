# CQRS Event Replay Repair — Debugging Task

## Overview

A CQRS event replay engine processes domain events from multiple aggregate streams (orders, inventory, payments), merges them into a deterministic global sequence, replays them through batch-based projections, and produces a materialized view with a summary report. The system handles cross-stream ordering and batch-boundary checkpointing.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, event data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system replays events through six stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format aggregate stream files from `/app/runtime/data/` for each stream listed in the active_aggregates configuration

2. *Sequencing* (`/app/runtime/sequencer.py`) — Merges events from all loaded streams into a single deterministic global order sorted by timestamp, then stream_id, then sequence number

3. *Batching* (`/app/runtime/batcher.py`) — Splits the sequenced event list into fixed-size batches according to the strict replay batch configuration for controlled processing

4. *Projection* (`/app/runtime/projector.py`) — Applies each batch of events through fold operations to build aggregate state, producing per-batch snapshots

5. *Materialization* (`/app/runtime/materializer.py`) — Assembles the final materialized view from batch snapshots using the configured snapshot mode (the strict configuration specifies latest-wins semantics)

6. *Summarization* (`/app/runtime/summarizer.py`) — Generates a summary report with per-stream statistics and an ordering verification hash

## Problem

The system produces output but with several anomalies:
- One of the three configured aggregate streams does not appear in the output
- Event totals in the materialized view appear inflated beyond expected values
- The ordering verification hash does not match the expected deterministic sequence
- Batch boundaries seem larger than the intended strict processing configuration

## Expected Correct Output

When all defects are resolved:
- All three streams (orders, inventory, payments) must be present in the materialized view
- Total events processed must equal 53 (19 + 18 + 16)
- Order total value must be exactly 815.25 (not inflated by batch accumulation)
- The ordering hash must be `d744fb63ad2a3a5a` reflecting deterministic cross-stream ordering
- Settled payment total must be 747.15

## Output Schema

### /app/runtime/output/materialized_view.json

| Field | Type | Description |
|-------|------|-------------|
| orders | object | Materialized state for orders aggregate |
| orders.event_count | integer | Number of order events processed |
| orders.entities | object | Map of order_id to current order state |
| orders.totals | object | Aggregate totals (total_order_value, order_count, delivered_count, cancelled_count) |
| inventory | object | Materialized state for inventory aggregate |
| inventory.event_count | integer | Number of inventory events processed |
| inventory.entities | object | Map of SKU to current stock state |
| inventory.totals | object | Aggregate totals (total_stock, total_reserved, total_damaged) |
| payments | object | Materialized state for payments aggregate |
| payments.event_count | integer | Number of payment events processed |
| payments.entities | object | Map of payment_id to current payment state |
| payments.totals | object | Aggregate totals (initiated_total, captured_total, refunded_total, total_fees, settled_total) |

### /app/runtime/output/replay_summary.json

| Field | Type | Description |
|-------|------|-------------|
| total_events_processed | integer | Total events across all streams |
| stream_count | integer | Number of streams in materialized view |
| streams | object | Per-stream statistics with event_count, entity_count, totals |
| ordering_hash | string | SHA-256 prefix hash of deterministic event ordering |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Replay parameters and stream configuration |
| /app/runtime/loader.py | Aggregate stream loading from data files |
| /app/runtime/sequencer.py | Cross-stream event ordering and merging |
| /app/runtime/batcher.py | Event batch splitting for replay |
| /app/runtime/projector.py | Batch event projection into aggregate state |
| /app/runtime/materializer.py | Snapshot-to-view materialization |
| /app/runtime/summarizer.py | Replay summary report generation |
| /app/runtime/run_replay.py | Main entry point orchestrating all stages |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
