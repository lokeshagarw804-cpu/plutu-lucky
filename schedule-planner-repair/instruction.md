# Schedule Planner Repair — Debugging Task

## Overview

A preemptive priority scheduling engine manages job execution across multiple submission queues (batch, interactive, realtime, maintenance). It loads job definitions, establishes a deterministic priority ordering, simulates round-robin execution with configurable time quanta, captures periodic progress snapshots, and validates execution consistency for correctness auditing.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, job data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Processing Stages

1. *Queue Loading* (`/app/runtime/queue_loader.py`) — Reads JSON job files from `/app/runtime/data/` for each configured queue. Only queues listed in the `active_queues` configuration value are loaded into the scheduler.

2. *Priority Sorting* (`/app/runtime/priority_sorter.py`) — Merges jobs from all loaded queues into a single deterministic execution order. The correct ordering is by priority descending, then deadline ascending, then queue_id alphabetically, then job_seq ascending within a queue. This ensures reproducible scheduling across runs.

3. *Execution* (`/app/runtime/executor.py`) — Simulates round-robin scheduling with a fixed time quantum per round. Each pending job receives one quantum per round until completed or max_rounds is reached.

4. *Progress Snapshots* (`/app/runtime/deadline_checker.py`) — Captures point-in-time execution progress at regular intervals (every 2 rounds). Each snapshot records the current accumulated execution time for each job at that moment.

5. *Validation* (`/app/runtime/plan_validator.py`) — Compares the executor's final state against the last progress snapshot. Uses the tolerance configured under `[scheduler.validation]` for determining acceptable differences between execution and snapshot tracking.

## Problem

The system produces output but exhibits several anomalies:
- The total number of scheduled jobs appears lower than expected given the configured queues
- Validation reports mismatches between execution results and progress snapshots
- Progress snapshot values grow unreasonably large across successive checkpoints
- Some job orderings in execution plans appear non-deterministic when jobs share priority and deadline values

## Expected Correct Output

When all defects are resolved:
- All 4 queues should be loaded (batch, interactive, realtime, maintenance) producing 50 total jobs
- The priority sorter should produce a stable deterministic ordering across runs
- Progress snapshots should reflect the exact accumulated execution time at each checkpoint
- Validation should report status "valid" with zero mismatches

## Output Schema

### /app/runtime/output/execution_plan.json

| Field | Type | Description |
|-------|------|-------------|
| total_jobs_scheduled | integer | Total number of jobs in schedule |
| total_queues | integer | Number of queues loaded |
| jobs_completed | integer | Jobs that finished within max_rounds |
| deadlines_met | integer | Jobs completing before their deadline |
| execution_results | array | Per-job execution state objects |
| execution_results[].job_id | string | Unique job identifier |
| execution_results[].queue_id | string | Source queue |
| execution_results[].priority | integer | Job priority level |
| execution_results[].deadline | integer | Deadline in ms |
| execution_results[].duration_ms | integer | Required execution time |
| execution_results[].executed_ms | integer | Actual time allocated |
| execution_results[].completed | boolean | Whether job finished |
| execution_results[].completion_round | integer or null | Round when completed |
| execution_results[].deadline_met | boolean or null | Whether deadline was satisfied |
| queues_loaded | array[string] | List of queue identifiers loaded |

### /app/runtime/output/progress_snapshots.json

| Field | Type | Description |
|-------|------|-------------|
| snapshot_interval_rounds | integer | Rounds between snapshots |
| total_snapshots | integer | Number of progress checkpoints |
| snapshots | array | List of snapshot checkpoint objects |
| snapshots[].round_number | integer | Round when snapshot was captured |
| snapshots[].jobs_completed | integer | Jobs done by this checkpoint |
| snapshots[].execution_progress | object | Map of job_id to ms executed so far |

### /app/runtime/output/validation_report.json

| Field | Type | Description |
|-------|------|-------------|
| total_jobs | integer | Jobs checked in validation |
| validated_jobs | integer | Jobs matching within tolerance |
| mismatches | array | List of mismatch objects |
| mismatches[].job_id | string | Job with mismatch |
| mismatches[].executor_ms | integer | Time from executor |
| mismatches[].snapshot_ms | float | Time from last snapshot |
| mismatches[].difference_ms | float | Absolute difference |
| status | string | "valid" or "mismatches_found" |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Queue selection, scheduling parameters, validation tolerance |
| /app/runtime/queue_loader.py | Loads jobs from configured submission queues |
| /app/runtime/priority_sorter.py | Establishes deterministic job execution ordering |
| /app/runtime/executor.py | Simulates round-robin execution with time quantum |
| /app/runtime/deadline_checker.py | Captures periodic execution progress snapshots |
| /app/runtime/plan_validator.py | Audits final execution state against snapshots |
| /app/runtime/run_scheduler.py | Main entry point orchestrating all stages |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
