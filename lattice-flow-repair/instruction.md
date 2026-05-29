# Lattice Flow Simulator - Debugging Task

## Overview

A lattice-based pipe flow simulator models pressure propagation across a network of junction nodes. Each junction maintains a pressure vector that tracks cumulative hydraulic knowledge across all nodes in the network. Events (pumping, surging, and coupling between neighbors) modify these vectors over time. The system replays a trace log of events, computes final pressure states, classifies flow relationships between junction pairs, determines hydraulic priority ordering, and generates a verification report.

## System Environment

- **Language**: Python 3.11
- **Runtime**: /app/runtime/ (source modules, trace data, output)
- **Global tooling**: uv and pytest are available
- **Dependencies**: Standard library only

## Architecture

The simulator processes events through a multi-stage pipeline:

1. **Trace Parsing** (`trace_parser.py`) - Reads the arrow-separated event log and produces structured event records.

2. **Pressure Engine** (`pressure_engine.py`) - Maintains per-junction pressure vectors. Applies pump events, surge events, and coupling events that propagate knowledge between connected junctions.

3. **Flow Analysis** (`flow_analyzer.py`) - Compares final pressure vectors across all junction pairs to classify flow relationships and compute priority ordering.

4. **Report Generation** (`report_writer.py`) - Assembles the final analysis report including junction summaries, pair classifications, priority ordering, network metrics, and a verification digest.

5. **Orchestration** (`orchestrator.py`) - Coordinates the full pipeline, writing results to `flow_state.jsonl` and `flow_report.json`.

## Problem

The system produces output but the results are incorrect. Running the test suite reveals multiple failures across pressure state verification, flow classification, and consistency checks. The defects produce a cascade of incorrect values through the pipeline.

## Expected Correct Behavior

When all defects are resolved:
- Pressure vectors reflect the complete activity history of each junction
- Flow independence classification correctly identifies the relationship between every junction pair
- Priority ordering ranks junctions by their actual hydraulic significance in the network
- The verification digest is consistent with all corrected computations
- All 14 tests pass

## Output Schema

### flow_state.jsonl

One JSON object per line, one per junction (sorted by junction ID):

| Field | Type | Description |
|-------|------|-------------|
| junction_id | string | Junction node identifier |
| pressure_vector | array[int] | Final pressure vector in sorted node order |
| pressure_map | object | Pressure state as {node_id: value} |
| event_count | integer | Number of trace events for this junction |

### flow_report.json

| Field | Type | Description |
|-------|------|-------------|
| junction_count | integer | Number of junctions (7) |
| junction_ids | array[string] | Sorted junction identifiers |
| junction_summaries | object | Per-junction summary with vector, sum, max, event_count, coupling_strength |
| flow_analysis | object | Pair classification results |
| flow_analysis.independent_pairs | array | List of independent (node_a, node_b) pairs |
| flow_analysis.independent_count | integer | Number of independent pairs |
| flow_analysis.dependent_count | integer | Number of dependent pairs |
| flow_analysis.total_pairs | integer | Total pairs analyzed (21) |
| priority_order | array[string] | Junctions ordered by hydraulic priority |
| cross_validation | object | Per-pair independence classification with divergence |
| network_metrics | object | Network-wide magnitude statistics |
| digest | string | 16-character hex verification digest |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/flow_trace.log | Event trace with 52 events across 7 junctions |
| /app/runtime/trace_parser.py | Parses arrow-separated trace format |
| /app/runtime/pressure_engine.py | Core pressure vector mechanics |
| /app/runtime/flow_analyzer.py | Flow independence and priority analysis |
| /app/runtime/report_writer.py | Report generation with network metrics and digest |
| /app/runtime/orchestrator.py | Main simulation entry point |

## Your Task

Identify and fix defects in the runtime source files so that all 14 tests pass. The defects produce incorrect pressure values, wrong pair classifications, and incorrect priority ordering.
