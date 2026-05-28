# Packet Flow Analyzer - Debugging Task

## Overview

A distributed intrusion detection system models observation propagation across a network of sensor nodes. Each sensor maintains an observation vector that tracks cumulative detection knowledge across all nodes in the mesh network. Events (scanning, probing, and synchronization between neighbors) modify these vectors over time. The system replays a capture log of events, computes final observation states, classifies flow relationships between sensor pairs, determines detection priority ordering, and generates a verification report.

## System Environment

- **Language**: Python 3.11
- **Runtime**: /app/runtime/ (source modules, capture data, output)
- **Global tooling**: uv and pytest are available
- **Dependencies**: Standard library only

## Architecture

The system processes events through a multi-stage pipeline:

1. **Log Parsing** (`log_parser.py`) - Reads the arrow-separated capture log and produces structured event records.

2. **Observation Engine** (`observation_engine.py`) - Maintains per-sensor observation vectors. Applies scan events, probe events, and synchronization events that propagate knowledge between connected sensors.

3. **Flow Classification** (`flow_classifier.py`) - Compares final observation vectors across all sensor pairs to classify flow relationships and compute priority ordering.

4. **Report Generation** (`report_generator.py`) - Assembles the final analysis report including sensor summaries, pair classifications, priority ordering, network metrics, and a verification digest.

5. **Orchestration** (`orchestrator.py`) - Coordinates the full pipeline, writing results to `flow_state.jsonl` and `flow_report.json`.

## Problem

The system produces output but the results are incorrect. Running the test suite reveals multiple failures across observation state verification, flow classification, and consistency checks. The defects produce a cascade of incorrect values through the pipeline.

## Expected Correct Behavior

When all defects are resolved:
- Observation vectors reflect the complete activity history of each sensor
- Flow independence classification correctly identifies the relationship between every sensor pair
- Priority ordering ranks sensors by their actual detection significance in the network
- The verification digest is consistent with all corrected computations
- All 14 tests pass

## Output Schema

### flow_state.jsonl

One JSON object per line, one per sensor (sorted by sensor ID):

| Field | Type | Description |
|-------|------|-------------|
| sensor_id | string | Sensor node identifier |
| observation_vector | array[int] | Final observation vector in sorted node order |
| observation_map | object | Observation state as {sensor_id: value} |
| event_count | integer | Number of capture events for this sensor |

### flow_report.json

| Field | Type | Description |
|-------|------|-------------|
| sensor_count | integer | Number of sensors (7) |
| sensor_ids | array[string] | Sorted sensor identifiers |
| sensor_summaries | object | Per-sensor summary with vector, sum, max, event_count, sync_strength |
| flow_analysis | object | Pair classification results |
| flow_analysis.independent_pairs | array | List of independent (node_a, node_b) pairs |
| flow_analysis.independent_count | integer | Number of independent pairs |
| flow_analysis.dependent_count | integer | Number of dependent pairs |
| flow_analysis.total_pairs | integer | Total pairs analyzed (21) |
| priority_order | array[string] | Sensors ordered by detection priority |
| cross_validation | object | Per-pair independence classification with divergence |
| network_metrics | object | Network-wide magnitude statistics |
| digest | string | 16-character hex verification digest |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/capture_log.dat | Event capture with 52 events across 7 sensors |
| /app/runtime/log_parser.py | Parses arrow-separated capture format |
| /app/runtime/observation_engine.py | Core observation vector mechanics |
| /app/runtime/flow_classifier.py | Flow independence and priority analysis |
| /app/runtime/report_generator.py | Report generation with network metrics and digest |
| /app/runtime/orchestrator.py | Main simulation entry point |

## Your Task

Identify and fix defects in the runtime source files so that all 14 tests pass. The defects produce incorrect observation values, wrong pair classifications, and incorrect priority ordering.
