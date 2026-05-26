# Task Scheduler Engine — Debugging Task

## Overview

A multi-queue task scheduling engine reads job definitions from priority-tiered queues, computes effective scheduling priorities across multiple rounds with aging factors, allocates execution time slots, and generates a deterministic execution plan. The system currently produces incorrect scheduling results.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source, config, data, output)
- *Global system-wide tooling*: uv and pytest are available

## Processing Stages

1. *Loading* — Reads task definitions from queue JSON files in /app/runtime/data/. Each file represents a distinct priority tier (critical, standard, batch, deferred) with its own task inventory.

2. *Queue Filtering* — Removes tasks from queues not in the configured active list. Only tasks belonging to active priority queues proceed to scheduling.

3. *Priority Computation* — Computes effective priority for each task across multiple scheduling rounds. Priority incorporates base value, deadline urgency, dependency readiness, and time-based aging. The weighted scheduling mode (section scheduling.weighted in /app/runtime/config.ini) uses a conservative aging factor of 0.08 for production workloads. Each round independently computes the effective priority for remaining tasks.

4. *Slot Allocation* — Assigns execution time slots based on priority ordering. Tasks with equal effective priority are ordered by queue identifier then task identifier for deterministic scheduling.

5. *Plan Output* — Produces execution plan, schedule matrix, and processing summary.

## Problem

The system runs without crashing but the execution plan has several issues:
- Some queue tiers are silently excluded from scheduling
- Priority values appear inflated beyond reasonable bounds
- The aging factor seems more aggressive than intended
- Execution ordering is non-deterministic for tasks with tied priorities

## Expected Correct Output

When functioning correctly:
- All 24 tasks from 4 queue tiers are scheduled
- Priority values remain bounded (below 200 for this dataset)
- Critical tasks appear first, deferred tasks last
- Tasks with equal effective priority are ordered by (queue_id, task_id)

## Output Schema

### /app/runtime/output/execution_plan.json

| Field | Type | Description |
|-------|------|-------------|
| total_scheduled | int | Number of tasks in the execution plan |
| entries | list | Ordered list of scheduled task slots |
| entries[].position | int | Zero-based position in execution sequence |
| entries[].task_id | string | Task identifier (local to each queue) |
| entries[].queue_id | string | Source queue identifier |
| entries[].effective_priority | float | Computed scheduling priority |
| entries[].start_minute | int | Scheduled start time in minutes |
| entries[].duration_minutes | int | Allocated execution duration |
| total_duration_minutes | int | Sum of all task durations |

### /app/runtime/output/schedule_matrix.json

| Field | Type | Description |
|-------|------|-------------|
| rounds | object | Priority evaluations grouped by scheduling round |
| total_evaluations | int | Total priority computations performed |

### /app/runtime/output/scheduler_summary.json

| Field | Type | Description |
|-------|------|-------------|
| total_tasks_input | int | Tasks received after filtering |
| total_scheduled | int | Tasks successfully scheduled |
| queues_processed | list | All queue types in input |
| queues_in_plan | list | Queue types with scheduled tasks |
| total_rounds | int | Number of scheduling rounds executed |
| by_queue | object | Scheduled task count per queue |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/run_scheduler.py | Main entry point |
| /app/runtime/loader.py | Reads task definitions from queue files |
| /app/runtime/queue_filter.py | Filters tasks by active queue membership |
| /app/runtime/priority_engine.py | Multi-round priority computation |
| /app/runtime/slot_allocator.py | Time slot assignment and ordering |
| /app/runtime/plan_writer.py | Output file generation |
| /app/runtime/config.ini | Scheduling configuration |
| /app/runtime/data/queue_critical.json | Critical priority tasks (6 records) |
| /app/runtime/data/queue_standard.json | Standard priority tasks (6 records) |
| /app/runtime/data/queue_batch.json | Batch processing tasks (6 records) |
| /app/runtime/data/queue_deferred.json | Deferred low-priority tasks (6 records) |

## Your Task

Identify and fix the defects in the runtime source files under /app/runtime/ that cause queue exclusion, priority inflation, incorrect aging parameters, and non-deterministic scheduling order.
