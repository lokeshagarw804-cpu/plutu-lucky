# Event Replay Materialization — Debugging Task

## Overview

This system replays event streams from an order management platform to build materialized aggregate views. It reads events from multiple sources (orders, payments, refunds), merges them into a unified timeline, projects aggregate state for each order, and writes summary reports. The system currently produces incorrect output due to several defects in the processing logic.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source, config, data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Entry point*: `python3 -m runtime.run_replay`

## Processing Stages

1. *Loading* — The loader reads event JSON files from /app/runtime/data/ and filters them based on the `event_streams` configuration in /app/runtime/config.ini under the `[sources]` section. Only streams listed in that config value are included.

2. *Correlation* — The correlator merges events from all loaded streams into a single ordered timeline. Events are sorted by timestamp, then by stream_id for stable cross-stream ordering, then by sequence number within each stream.

3. *Projection* — The projector replays the ordered events in batches to build aggregate state for each order. The batch size is configured under the `[projection.incremental]` section. When an order appears in multiple batches, the final snapshot values should replace earlier ones (last-write-wins semantics) for numeric accumulators.

4. *Materialization* — The materializer writes two output files: an aggregate summary and an event timeline to /app/runtime/output/.

## Problem

The system runs without errors but produces incorrect output:
- Some event streams appear to be missing from the output entirely
- Financial totals (payments, refunds, net revenue) are inflated beyond expected values
- Event timeline ordering is nondeterministic when events from different streams share the same timestamp
- The number of processed events does not match what the input data contains

## Expected Correct Output

When all defects are fixed, the system should produce:
- An aggregate summary covering all 7 orders from 3 event streams (24 total events)
- Correct net revenue of 340.00 across all orders
- Deterministic timeline ordering where same-timestamp events are sorted by stream_id alphabetically
- All orders with refunds showing status "partially_refunded"

## Output Schema

### /app/runtime/output/aggregate_summary.json

| Field | Type | Description |
|-------|------|-------------|
| generated_at | string | ISO timestamp of generation |
| total_orders | integer | Number of unique orders processed |
| total_events_processed | integer | Total events across all orders |
| total_net_revenue | float | Sum of net_revenue for all orders |
| orders | array | List of per-order aggregate objects |

#### orders[] element

| Field | Type | Description |
|-------|------|-------------|
| order_id | string | Unique order identifier |
| customer | string | Customer name |
| item_count | integer | Number of line items in the order |
| total_amount | float | Gross order amount from item prices |
| payment_amount | float | Amount received via payment |
| refund_amount | float | Amount refunded |
| net_revenue | float | payment_amount minus refund_amount |
| status | string | Current order status |
| event_count | integer | Number of events for this order |

### /app/runtime/output/event_timeline.json

| Field | Type | Description |
|-------|------|-------------|
| total_events | integer | Total number of events in the timeline |
| entries | array | Ordered list of timeline entry objects |

#### entries[] element

| Field | Type | Description |
|-------|------|-------------|
| position | integer | 1-based position in the timeline |
| event_id | string | Unique event identifier |
| stream_id | string | Source stream name |
| timestamp | string | ISO timestamp of the event |
| type | string | Event type name |
| order_id | string | Associated order identifier |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/run_replay.py | Main entry point, orchestrates all stages |
| /app/runtime/loader.py | Loads and filters event streams from disk |
| /app/runtime/correlator.py | Merges events into unified timeline ordering |
| /app/runtime/projector.py | Builds aggregate state from event batches |
| /app/runtime/materializer.py | Writes final output JSON files |
| /app/runtime/config.ini | Configuration for all processing stages |
| /app/runtime/data/ | Source event stream JSON files |

## Your Task

Identify and fix the defects in the runtime source files under /app/runtime/ so that the materialization system produces correct output matching the schema and expected values documented above. The defects span multiple modules and interact with the configuration.
