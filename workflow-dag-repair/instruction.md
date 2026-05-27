# Workflow DAG Execution Engine — Debugging Task

## Overview

A workflow DAG execution engine ingests job definitions from multiple workflow files, resolves inter-job dependencies via topological sorting, schedules jobs into discrete time slots respecting parallelism limits, and tracks resource utilization across all pools. The system handles concurrent workflows with shared submission timestamps and produces both an execution timeline and a resource utilization report.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, workflow data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes workflow data through five stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format workflow files from `/app/runtime/data/`, each containing a DAG of job definitions with dependencies, priorities, and resource requirements.

2. *Dependency Resolution* (`/app/runtime/resolver.py`) — Performs topological sort across all workflow DAGs. Among ready jobs (zero in-degree), ordering is determined by priority tier first, then submission timestamp, then workflow identifier alphabetically for deterministic results.

3. *Time Slot Scheduling* (`/app/runtime/scheduler.py`) — Assigns each job to consecutive time slots respecting the strict parallelism limit from the `scheduling.strict` configuration section. Production workloads must use the strict limit to avoid resource contention.

4. *Resource Tracking* (`/app/runtime/tracker.py`) — Computes per-slot resource consumption for each configured pool. Reports the peak single-slot usage for each resource pool (not cumulative across slots).

5. *Report Generation* (`/app/runtime/reporter.py`) — Assembles execution timeline and resource utilization report JSON files.

## Problem

The system generates output but exhibits several anomalies:
- Jobs appear to be scheduled with too much parallelism, completing in far fewer time slots than expected for the workload size
- Resource utilization percentages exceed 100% for CPU, memory, and GPU pools despite the data being designed to fit within limits
- Network resource usage shows as zero even though several jobs declare network requirements
- Job ordering between workflows with identical priorities and submission times varies unpredictably across runs

## Expected Correct Output

When all defects are resolved:
- No time slot should have more than 3 concurrent jobs (the strict parallelism limit)
- Total scheduling span should be at least 18 time slots for 55 jobs with max 3 parallel
- All four resource pools (cpu, memory, gpu, network) should show non-zero utilization
- Peak utilization for each pool should remain within configured limits (cpu≤100, memory≤256, gpu≤4, network≤1000)
- Jobs from workflow "alpha" should be scheduled before "beta" when both share the same priority tier and submission timestamp

## Output Schema

### /app/runtime/output/execution_timeline.json

| Field | Type | Description |
|-------|------|-------------|
| total_jobs | integer | Total number of scheduled jobs |
| total_workflows | integer | Number of distinct workflows processed |
| workflows | array | Per-workflow summary objects |
| workflows[].workflow_id | string | Workflow identifier |
| workflows[].job_count | integer | Number of jobs in this workflow |
| workflows[].total_slots | integer | Latest end slot + 1 for this workflow |
| schedule | array | Ordered list of scheduled job entries |
| schedule[].job_id | string | Unique job identifier |
| schedule[].workflow_id | string | Parent workflow identifier |
| schedule[].priority | string | Priority tier (critical/high/medium/low) |
| schedule[].start_slot | integer | First assigned time slot |
| schedule[].end_slot | integer | Last assigned time slot |
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
| /app/runtime/config.ini | Scheduling parameters, resource pool configuration |
| /app/runtime/loader.py | Workflow definition loading |
| /app/runtime/resolver.py | DAG dependency resolution and topological ordering |
| /app/runtime/scheduler.py | Time slot assignment with parallelism constraints |
| /app/runtime/tracker.py | Resource utilization tracking across pools |
| /app/runtime/reporter.py | Output report generation |
| /app/runtime/run_workflow.py | Main entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect scheduling and resource tracking results.
