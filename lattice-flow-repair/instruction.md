# Lattice Flow Simulator Repair - Debugging Task

## Overview

A lattice-based pipe flow simulator models pressure propagation across a network of junction nodes. Each junction maintains a pressure vector that tracks cumulative hydraulic knowledge across all nodes in the network. Events (pumping, surging, and coupling between neighbors) modify these vectors over time. The system replays a trace log of events, computes final pressure states, classifies flow relationships between junction pairs, determines hydraulic priority ordering, and generates a verification report.

## System Environment

- **Language**: Python 3.11
- **Runtime**: /app/runtime/ (source modules, trace data, output)
- **Global tooling**: uv and pytest are available
- **Dependencies**: Standard library only

## Architecture

The simulator processes events through four stages:

1. **Trace Parsing** (`/app/runtime/trace_parser.py`) - Reads the arrow-separated event log from `/app/runtime/flow_trace.log` and produces structured event records.

2. **Pressure Engine** (`/app/runtime/pressure_engine.py`) - Maintains per-junction pressure vectors. Applies pump events (+1 to own component), surge events (+2 to own component), and coupling events (merging neighbor knowledge into the local vector).

3. **Flow Analysis** (`/app/runtime/flow_analyzer.py`) - Compares final pressure vectors across all junction pairs to determine which flows evolved independently versus which show evidence of dominance relationships. Also computes a priority ordering reflecting hydraulic significance.

4. **Report Generation** (`/app/runtime/report_writer.py`) - Assembles the final analysis report including junction summaries, pair classifications, priority ordering, and a verification digest.

5. **Orchestration** (`/app/runtime/orchestrator.py`) - Coordinates the full pipeline, writing results to `/app/runtime/flow_state.jsonl` (per-junction state) and `/app/runtime/flow_report.json` (analysis report).

## Problem

The system produces output but exhibits several anomalies:

- Pressure vectors show unexpected values after coupling events between junctions. Junctions that participate in coupling operations appear to have lower own-component pressure than their event history would suggest.
- Flow independence classification produces fewer independent pairs than expected for a network where most junctions evolved largely in isolation from each other.
- Priority ordering does not reflect actual hydraulic significance of junctions in the network. Junctions with clearly higher accumulated pressure activity are ranked below less active junctions.

## Expected Correct Behavior

When all defects are resolved:
- Each junction's own-component pressure should reflect all local activity including participation in coupling operations
- Flow independence should correctly identify pairs where neither junction's pressure history contains evidence of dominating the other
- Priority ordering should rank junctions by their actual accumulated hydraulic significance across the entire network
- The verification digest should be consistent with all corrected computations

## Output Schema

### /app/runtime/flow_state.jsonl

One JSON object per line, one per junction (sorted by junction ID):

| Field | Type | Description |
|-------|------|-------------|
| junction_id | string | Junction node identifier |
| pressure_vector | array[int] | Final pressure vector in sorted node order |
| pressure_map | object | Pressure state as {node_id: value} |
| event_count | integer | Number of trace events for this junction |

### /app/runtime/flow_report.json

| Field | Type | Description |
|-------|------|-------------|
| junction_count | integer | Number of junctions (7) |
| junction_ids | array[string] | Sorted junction identifiers |
| junction_summaries | object | Per-junction summary with vector, sum, max, event_count |
| flow_analysis | object | Pair classification results |
| flow_analysis.independent_pairs | array | List of independent (node_a, node_b) pairs |
| flow_analysis.independent_count | integer | Number of independent pairs |
| flow_analysis.dependent_count | integer | Number of dependent pairs |
| flow_analysis.total_pairs | integer | Total pairs analyzed (21) |
| priority_order | array[string] | Junctions ordered by hydraulic priority |
| cross_validation | object | Per-pair independence classification |
| digest | string | 16-character hex verification digest |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/flow_trace.log | Event trace with 45 events across 7 junctions |
| /app/runtime/trace_parser.py | Parses arrow-separated trace format |
| /app/runtime/pressure_engine.py | Core pressure vector mechanics |
| /app/runtime/flow_analyzer.py | Flow independence and priority analysis |
| /app/runtime/report_writer.py | Report generation with digest |
| /app/runtime/orchestrator.py | Main simulation entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results. The trace parser and orchestrator are functioning correctly.
