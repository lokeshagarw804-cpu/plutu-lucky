# Task Scheduler Repair — Debugging Task

## Overview

A priority-based task scheduler reads job definitions from multiple worker queues, computes weighted priority scores, assigns jobs to resource-bounded execution batches, checks deadline compliance, and generates a resource utilization report. The system handles heterogeneous worker types and produces both an execution manifest and a utilization breakdown.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, job data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes job queues through five stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format queue files from `/app/runtime/data/`, filtering to only active worker types defined in config

2. *Priority Scoring* (`/app/runtime/priority_scorer.py`) — Computes weighted composite score for each job using urgency, resource cost, and age factors, then sorts descending by score. For equal scores at the same timestamp, ties are broken by queue_id alphabetically then by seq number within that queue.

3. *Batch Scheduling* (`/app/runtime/batch_scheduler.py`) — Assigns priority-sorted jobs to sequential batches, each bounded by the capacity limit from the `scheduling.precise` configuration section

4. *Deadline Checking* (`/app/runtime/deadline_checker.py`) — Computes execution timing for each batch based on the deadline window multiplied by the batch's total resource units

5. *Resource Tracking* (`/app/runtime/resource_tracker.py`) — Produces per-batch resource snapshots showing each batch's independent allocation, plus aggregate totals per worker type

## Problem

The system produces output but with several anomalies:
- Fewer jobs appear in the schedule than expected given the queue data files present
- Batch counts and sizes do not match expectations for the configured capacity
- Some job pairs with identical priority scores appear in non-deterministic order
- Resource utilization snapshots show suspiciously growing values across batches
- Total execution duration is slightly off from the expected arithmetic

## Expected Correct Output

When all defects are resolved:
- All 53 jobs from 3 active queues (compute: 18, io: 15, gpu: 20) must be scheduled
- Jobs are assigned to 12 batches with capacity 12 resource units each
- The scheduling order must be deterministic: c016 comes before g011 (same score, queue_id breaks tie)
- Each batch snapshot shows only that batch's resource allocation (not cumulative)
- Total duration is exactly 1270 time units (10 * 127 total resource units)
- Active worker types are: compute, gpu, io

## Output Schema

### /app/runtime/output/execution_manifest.json

| Field | Type | Description |
|-------|------|-------------|
| total_jobs | integer | Total number of scheduled jobs |
| total_batches | integer | Number of execution batches |
| batches | array | List of batch objects |
| batches[].batch_id | integer | Sequential batch identifier |
| batches[].job_count | integer | Jobs in this batch |
| batches[].total_resource_units | integer | Resource units consumed |
| batches[].utilization | float | Fraction of capacity used |
| batches[].jobs | array[string] | Job IDs assigned to batch |
| batches[].capacity | integer | Batch capacity limit |
| scheduling_order | array[string] | All job IDs in priority order |
| timing | object | Deadline timing analysis |
| timing.total_batches | integer | Number of timed batches |
| timing.batch_timing | array | Per-batch timing records |
| timing.batch_timing[].batch_id | integer | Batch identifier |
| timing.batch_timing[].start_time | integer | Batch start timestamp |
| timing.batch_timing[].end_time | integer | Batch end timestamp |
| timing.batch_timing[].duration | integer | Batch execution duration |
| timing.total_duration | integer | Sum of all batch durations |
| batches[].utilization | float | Fraction of capacity used (0 to 1) |

### /app/runtime/output/utilization_report.json

| Field | Type | Description |
|-------|------|-------------|
| total_resource_units | integer | Sum of all resource units |
| per_type_totals | object | Resource units per worker type |
| batch_count | integer | Number of batches |
| batch_snapshots | array[object] | Per-batch resource breakdown |
| active_worker_types | array[string] | Sorted list of worker types |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Scheduling parameters and worker configuration |
| /app/runtime/loader.py | Queue data loading with worker type filtering |
| /app/runtime/priority_scorer.py | Weighted priority computation and sorting |
| /app/runtime/batch_scheduler.py | Resource-bounded batch assignment |
| /app/runtime/deadline_checker.py | Batch timing computation |
| /app/runtime/resource_tracker.py | Per-batch resource utilization tracking |
| /app/runtime/run_scheduler.py | Main entry point and orchestration |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
