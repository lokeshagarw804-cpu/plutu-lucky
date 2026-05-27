# Workflow DAG Execution Engine — Debugging Task

## Overview

A workflow DAG execution engine ingests job definitions from multiple workflow files, resolves inter-job dependencies via topological sorting, schedules jobs into discrete time slots with concurrency constraints, and tracks resource utilization across all configured pools. The system handles concurrent workflows submitted at overlapping timestamps and produces both an execution timeline and a resource utilization report.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, workflow data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes workflow data through five stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format workflow files from `/app/runtime/data/`, each containing a DAG of job definitions with dependencies, priorities, and resource requirements.

2. *Dependency Resolution* (`/app/runtime/resolver.py`) — Performs topological sort across all workflow DAGs using Kahn's algorithm. Among ready jobs (zero in-degree), the resolution order is determined by the configured priority tiers, then submission timestamp, then workflow identifier for fully deterministic results.

3. *Time Slot Scheduling* (`/app/runtime/scheduler.py`) — Assigns each job to consecutive time slots. The scheduler must enforce the concurrency limit appropriate for the deployment mode configured in the system.

4. *Resource Tracking* (`/app/runtime/tracker.py`) — Computes per-slot resource consumption for each configured pool. The tracking mode determines how pool-level statistics are aggregated from slot-level data.

5. *Report Generation* (`/app/runtime/reporter.py`) — Assembles execution timeline and resource utilization report JSON files. Workflow makespan represents the total number of time slots from start to completion.

## Problem

The system generates output but exhibits several anomalies:
- Far too many jobs execute simultaneously, completing in fewer time slots than the workload should require
- Resource utilization percentages exceed physical pool capacities for several resources
- One resource pool consistently reports zero usage despite jobs declaring requirements for it
- Job ordering across workflows with equal priority and submission time is not deterministic
- Workflow makespan values appear to be slightly lower than expected

## Expected Correct Output

When all defects are resolved:
- Concurrency must not exceed the production limit (3 jobs per time slot)
- Total schedule span should be at least 18 time slots for 55 jobs under the production constraint
- All four resource pools (cpu, memory, gpu, network) should report non-zero utilization
- No pool's peak usage should exceed its configured capacity limit
- Workflows submitted at the same timestamp must be ordered alphabetically by identifier when priorities tie
- Workflow makespan should equal one plus the latest end_slot of any job in that workflow

## Output Schema

### /app/runtime/output/execution_timeline.json

| Field | Type | Description |
|-------|------|-------------|
| total_jobs | integer | Total number of scheduled jobs |
| total_workflows | integer | Number of distinct workflows processed |
| workflows | array | Per-workflow summary objects |
| workflows[].workflow_id | string | Workflow identifier |
| workflows[].job_count | integer | Number of jobs in this workflow |
| workflows[].makespan | integer | Slots from first to last completion (end_slot + 1) |
| schedule | array | Ordered list of scheduled job entries |
| schedule[].job_id | string | Unique job identifier |
| schedule[].workflow_id | string | Parent workflow identifier |
| schedule[].priority | string | Priority tier (critical/high/medium/low) |
| schedule[].start_slot | integer | First assigned time slot |
| schedule[].end_slot | integer | Last assigned time slot (inclusive) |
| schedule[].slots_used | integer | Number of slots consumed |
| schedule[].resources | object | Resource demands for this job |

### /app/runtime/output/resource_report.json

| Field | Type | Description |
|-------|------|-------------|
| total_slots | integer | Total time slots in the schedule |
| pools | object | Per-pool utilization summary |
| pools[name].peak_usage | number | Maximum usage in any single slot |
| pools[name].limit | integer | Configured pool capacity |
| pools[name].utilization_pct | number | Peak as percentage of limit |
| slot_count | integer | Number of slot breakdown entries |
| slot_breakdown | array | Per-slot resource usage detail |
| slot_breakdown[].slot | integer | Time slot index |
| slot_breakdown[].usage | object | Resource usage map for this slot |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Scheduling parameters and resource pool configuration |
| /app/runtime/loader.py | Workflow definition loading |
| /app/runtime/resolver.py | DAG dependency resolution and topological ordering |
| /app/runtime/scheduler.py | Time slot assignment with concurrency constraints |
| /app/runtime/tracker.py | Resource utilization tracking across pools |
| /app/runtime/reporter.py | Output report generation |
| /app/runtime/run_workflow.py | Main entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect scheduling and resource tracking results.
