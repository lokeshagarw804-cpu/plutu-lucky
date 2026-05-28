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
| test_lattice_propagation.py | Validation test suite (14 tests) |

## Signal Event Types

- **PULSE**: Gradual signal accumulation from ambient lattice field
- **BURST**: High-energy signal spike from resonance event
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

## Expected Behavior

When functioning correctly, the pipeline should:
1. Accurately track signal depths through all event types
2. Correctly identify isolated signal paths between node pairs
3. Produce a priority ordering that reflects accumulated signal strength
4. Generate a consistent digest fingerprint of the propagation state

## Running

```
python3 /app/runtime/pipeline.py
```

## Validation

```
uv run --with pytest pytest -v /tests/test_lattice_propagation.py
```
