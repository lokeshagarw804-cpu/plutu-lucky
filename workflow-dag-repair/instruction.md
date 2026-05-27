# Workflow DAG Scheduler — Debugging Task

## Overview

A DAG-based workflow execution engine takes a directed acyclic graph of task nodes with dependencies, computes an execution schedule that respects parallelism constraints and topological ordering, and produces an audit trail. The system is used for orchestrating multi-stage build and deployment processes where tasks have priority weights, dependency chains, and resource costs.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, data files, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Processing Stages

1. *Graph Loading* (`/app/runtime/loader.py`) — Reads the workflow DAG definition from `/app/runtime/data/workflow_graph.json`, resource limits, and priority overrides. Builds a mapping from priority level names to numeric scheduling weights using configuration entries.

2. *Dependency Resolution* (`/app/runtime/resolver.py`) — Tracks execution state for each node and determines which nodes have all predecessors satisfied. A node becomes schedulable when every upstream dependency has reached its terminal execution state. The execution state set on completion must match what the readiness check expects.

3. *Priority Calculation* (`/app/runtime/prioritizer.py`) — Computes effective scheduling priority for each node based on its base weight, a critical path cost factor, optional boost overrides, and topological depth decay. The critical path cost through a node represents the bottleneck predecessor chain — the longest weighted path reaching that node. Nodes are ranked by effective priority descending; ties at the same priority level are broken by topological depth (deeper nodes first), then alphabetically.

4. *Schedule Building* (`/app/runtime/scheduler.py`) — Iteratively assigns ready nodes to time-slots. Each slot has a maximum concurrency limit defined under the constrained scheduler configuration. Nodes are selected from the ranked ready pool until the slot fills or no more ready nodes exist, then the slot advances.

5. *Audit Output* (`/app/runtime/audit_writer.py`) — Serializes the execution schedule (slot assignments, node metadata) and audit summary (scheduled/unscheduled counts, critical node list) to JSON.

## Problem

The scheduler executes without errors but produces an incomplete and incorrect schedule:
- Many nodes never get scheduled despite having satisfiable dependencies
- Priority weights for some importance levels don't appear to take effect
- The concurrency limit doesn't match the constrained operating parameters
- Computed path costs for deeply-nested nodes seem inflated compared to expectation
- The scheduling appears to stall after processing only the root wave

## Expected Correct Output

When all defects are resolved:
- All 15 workflow nodes should be scheduled across multiple time-slots
- No nodes should remain in the unscheduled list
- The parallelism limit should reflect the constrained configuration
- Critical-priority nodes should have significantly higher effective priority than medium or low nodes
- The critical path cost for multi-dependency nodes should reflect the bottleneck (longest) predecessor chain
- Dependency ordering must be strictly respected across slots

## Output Schema

### /app/runtime/output/execution_schedule.json

| Field | Type | Description |
|-------|------|-------------|
| workflow_id | string | Workflow identifier |
| total_nodes | integer | Total nodes in the DAG |
| total_slots | integer | Number of time-slots in schedule |
| max_parallelism | integer | Configured concurrency limit |
| slots | array | List of time-slot objects |
| slots[].slot_index | integer | Zero-based slot position |
| slots[].nodes | array | Nodes assigned to this slot |
| slots[].nodes[].node_id | string | Node identifier |
| slots[].nodes[].priority | string | Original priority level |
| slots[].nodes[].effective_priority | float | Computed scheduling priority |
| slots[].nodes[].depth | integer | Topological depth from root |
| slots[].nodes[].critical_cost | integer | Critical path cost to this node |
| slots[].nodes[].cost | integer | Node execution cost |
| slots[].node_count | integer | Nodes in this slot |

### /app/runtime/output/audit_trail.json

| Field | Type | Description |
|-------|------|-------------|
| workflow_id | string | Workflow identifier |
| total_nodes | integer | Total workflow nodes |
| scheduled_count | integer | Nodes successfully scheduled |
| unscheduled_count | integer | Nodes not scheduled |
| unscheduled_nodes | array[string] | IDs of unscheduled nodes |
| slot_count | integer | Total time-slots |
| max_parallelism_used | integer | Parallelism setting applied |
| critical_nodes | array[string] | Nodes with critical priority |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Scheduler parameters, priority weights, execution settings |
| /app/runtime/loader.py | Reads DAG definition and builds priority weight mapping |
| /app/runtime/resolver.py | Tracks node state, determines dependency readiness |
| /app/runtime/prioritizer.py | Computes effective priority and critical path costs |
| /app/runtime/scheduler.py | Assigns nodes to time-slots with concurrency limits |
| /app/runtime/audit_writer.py | Writes schedule and audit JSON output |
| /app/runtime/run_scheduler.py | Main orchestration entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the scheduler produces a complete and correct execution schedule. Multiple modules contain interacting defects — fixing one in isolation may expose or mask issues in another.
