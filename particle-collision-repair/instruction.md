# Lattice Signal Propagation Simulator

## Overview

This system simulates signal propagation across a lattice of 7 sensor nodes (n0 through n6). Each node maintains a depth vector tracking accumulated signal levels from every node in the network. The pipeline reads a signal trace log, processes events through the propagation core, and produces a synthesis report with isolation classification and priority ordering.

## Architecture

All source modules are located under `/app/runtime/`. The test suite is under `/tests/`.

| Module | Role |
|--------|------|
| signal_trace.log | Input data containing 45 signal events |
| trace_reader.py | Parses the log into structured event records |
| propagation_core.py | Maintains per-node depth vectors and processes signal events |
| lattice_analysis.py | Computes isolation pairs and propagation priority rankings |
| synthesis_output.py | Generates the final JSON report with digest |
| calibration.py | Offline calibration utilities (not part of the live pipeline) |
| pipeline.py | Orchestrates the full simulation |

## Signal Event Types

- **PULSE**: Gradual signal accumulation from ambient lattice field (+1 to own depth component)
- **BURST**: High-energy signal spike from resonance event (+2 to own depth component)
- **RELAY**: Signal absorption from neighboring sensors via component-wise maximum

## Problem

The synthesis report does not match expected values. Investigation suggests the depth tracking and analytical modules may contain errors that affect the final output.

## Files with Potential Issues

- `/app/runtime/propagation_core.py` (signal depth tracking logic)
- `/app/runtime/lattice_analysis.py` (isolation classification and priority ranking)

## Files Known to be Correct

- `/app/runtime/trace_reader.py`
- `/app/runtime/pipeline.py`
- `/app/runtime/calibration.py`
- `/app/runtime/synthesis_output.py`

## Output Files

The pipeline produces two output files:

1. `/app/runtime/propagation_state.jsonl` — one JSON record per line, one line per sensor node
2. `/app/runtime/synthesis_report.json` — analysis report with isolation pairs, priority ordering, and digest

## Output Schema

### /app/runtime/propagation_state.jsonl

Each line is a JSON object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| node_id | string | Sensor node identifier (n0 through n6) |
| depth_vector | object | Maps each node_id to its integer depth value |
| total_depth | integer | Sum of all depth vector components |
| event_count | integer | Number of events processed by this node |

### /app/runtime/synthesis_report.json

| Field | Type | Description |
|-------|------|-------------|
| isolated_pairs | array[array[string]] | List of [node_a, node_b] pairs with isolated signal paths |
| isolated_pair_count | integer | Number of isolated pairs found |
| priority_order | array[string] | Node IDs sorted by propagation priority (highest first) |
| digest | string | 16-character hex MD5 fingerprint of canonical propagation state |

## Expected Correct Output

When all defects are resolved:
- Node n0 should have a self-depth (depth_vector.n0) of 15 after processing all 9 of its events
- Node n5 should have a total_depth of 47
- The isolation analysis should find 21 isolated pairs (all C(7,2) pairs are isolated since each node has its own peak depth component)
- The priority order should be: n0, n5, n1, n2, n3, n4, n6 (sorted by total accumulated depth, descending)
- The digest fingerprint should be `b60a42d61586d560`
- Priority ordering must reflect total accumulated signal strength, not recency of activity

## Running

```
python3 /app/runtime/pipeline.py
```

## Validation

```
uv run --with pytest pytest -v /tests/test_lattice_propagation.py
```
