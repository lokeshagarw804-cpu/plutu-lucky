# Type Inference Constraint Solver Repair

## Overview

A type inference constraint solver pipeline has three bugs causing incorrect outputs. Your task is to identify and fix all bugs so the test suite passes completely.

The pipeline solves type inference constraints for a simple expression language with 7 type variables (`t0`-`t6`). Each type variable maintains a constraint vector tracking accumulated inference constraints from every other variable in the system.

## Architecture

| File | Role |
|------|------|
| `/app/runtime/constraint_log.dat` | Input: 45 constraint events in pipe-separated format |
| `/app/runtime/log_reader.py` | Parses constraint log into structured event records |
| `/app/runtime/type_engine.py` | Constraint tracking with BIND, PROPAGATE, UNIFY events |
| `/app/runtime/type_analyzer.py` | Type compatibility classification and priority ranking |
| `/app/runtime/report_writer.py` | Generates final inference report (JSON) |
| `/app/runtime/orchestrator.py` | Orchestrates the full inference pipeline |
| `/app/runtime/calibration.py` | Offline calibration utilities (not used in pipeline) |

## Event Types

- **BIND**: Direct constraint addition (+1 to own constraint component)
- **PROPAGATE**: Strong constraint propagation (+2 to own constraint component)
- **UNIFY**: Constraint set absorption from peer type variable via component-wise maximum, with coupling gain from unification synchronization

## Problem Statement

The pipeline produces incorrect constraint state and inference report outputs. Three bugs exist across two source files. The test suite validates correctness at multiple levels:

1. **Structural tests** (8): Verify output files exist and have correct shape
2. **Constraint accuracy tests** (2): Verify constraint calculations
3. **Analysis accuracy tests** (2): Verify compatibility and priority logic
4. **Integrity tests** (2): Verify overall report consistency

Currently 8 tests pass (structural) and 6 fail (constraint, analysis, integrity).

## Files With Potential Issues

- `/app/runtime/type_engine.py`
- `/app/runtime/type_analyzer.py`

## Files Known Correct

- `/app/runtime/log_reader.py`
- `/app/runtime/orchestrator.py`
- `/app/runtime/calibration.py`
- `/app/runtime/report_writer.py`

## Output Schema

### type_state.jsonl

One JSON record per line, one per type variable:
```json
{"type_id": "t0", "constraint_vector": {"t0": ..., "t1": ..., ...}, "total_constraints": ..., "event_count": ...}
```

### inference_report.json

```json
{
  "compatible_pairs": [["t0", "t1"], ...],
  "compatible_pair_count": 21,
  "priority_order": ["t0", "t5", "t1", "t2", "t3", "t4", "t6"],
  "digest": "3fed9282152e0234"
}
```

## Expected Values

When all bugs are fixed:
- `t0` self-constraint (`constraint_vector.t0` for type t0) = **16**
- `t5` total constraints = **47**
- Compatible pair count = **21**
- Priority ordering must reflect total accumulated constraint strength: `['t0', 't5', 't1', 't2', 't3', 't4', 't6']`
- Digest = `3fed9282152e0234`

## Running the Pipeline

```bash
python3 /app/runtime/orchestrator.py
```

## Running Tests

```bash
uv run --with pytest pytest -v /tests/test_type_inference.py
```
