# Particle Collision Repair

## Overview

A lattice signal propagation simulation pipeline has three bugs causing incorrect outputs. Your task is to identify and fix all bugs so the test suite passes completely.

The pipeline simulates signal propagation through a lattice of 7 sensor nodes (`n0`-`n6`). Each node maintains a depth vector tracking accumulated signal strength from every other node in the lattice.

## Architecture

| File | Role |
|------|------|
| `/app/runtime/signal_trace.log` | Input: 45 sensor events in arrow-separated format |
| `/app/runtime/trace_reader.py` | Parses trace log into structured event records |
| `/app/runtime/propagation_core.py` | Signal depth tracking with PULSE, BURST, RELAY events |
| `/app/runtime/lattice_analysis.py` | Signal isolation classification and priority ranking |
| `/app/runtime/synthesis_output.py` | Generates final synthesis report (JSON) |
| `/app/runtime/pipeline.py` | Orchestrates the full simulation |
| `/app/runtime/calibration.py` | Offline calibration utilities (not used in pipeline) |

## Event Types

- **PULSE**: Gradual signal accumulation (+1 to own depth component)
- **BURST**: High-intensity signal spike (+2 to own depth component)
- **RELAY**: Signal absorption from neighboring sensors via component-wise maximum, with coupling gain from resonant synchronization

## Problem Statement

The pipeline produces incorrect propagation state and synthesis report outputs. Three bugs exist across two source files. The test suite validates correctness at multiple levels:

1. **Structural tests** (8): Verify output files exist and have correct shape
2. **Depth accuracy tests** (2): Verify signal depth calculations
3. **Analysis accuracy tests** (2): Verify isolation and priority logic
4. **Integrity tests** (2): Verify overall report consistency

Currently 8 tests pass (structural) and 6 fail (depth, analysis, integrity).

## Files With Potential Issues

- `/app/runtime/propagation_core.py`
- `/app/runtime/lattice_analysis.py`

## Files Known Correct

- `/app/runtime/trace_reader.py`
- `/app/runtime/pipeline.py`
- `/app/runtime/calibration.py`
- `/app/runtime/synthesis_output.py`

## Output Schema

### propagation_state.jsonl

One JSON record per line, one per node:
```json
{"node_id": "n0", "depth_vector": {"n0": ..., "n1": ..., ...}, "total_depth": ..., "event_count": ...}
```

### synthesis_report.json

```json
{
  "isolated_pairs": [["n0", "n1"], ...],
  "isolated_pair_count": 21,
  "priority_order": ["n0", "n5", "n1", "n2", "n3", "n4", "n6"],
  "digest": "54784ba07076c2ca"
}
```

## Expected Values

When all bugs are fixed:
- `n0` self-depth (`depth_vector.n0` for node n0) = **16**
- `n5` total depth = **47**
- Isolated pair count = **21**
- Priority ordering must reflect total accumulated signal strength: `['n0', 'n5', 'n1', 'n2', 'n3', 'n4', 'n6']`
- Digest = `54784ba07076c2ca`

## Running the Pipeline

```bash
python3 /app/runtime/pipeline.py
```

## Running Tests

```bash
uv run --with pytest pytest -v /tests/test_lattice_propagation.py
```
