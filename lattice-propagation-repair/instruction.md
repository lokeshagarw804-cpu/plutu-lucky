<!-- PLUTU-LUCKY-CANARY -->

# Lattice Signal Propagation Repair

## Overview

A lattice-based signal propagation simulator is producing anomalous results in its synthesis report. The system models electromagnetic signal propagation through a 7-node directed lattice network, computing attenuation, phase accumulation, interference patterns, and temporal alignment of multi-path arrivals.

## System Architecture

The simulator consists of several interconnected modules:

- `/app/runtime/propagation_core.py` - Signal propagation through multi-hop paths (attenuation, phase, delay)
- `/app/runtime/lattice_analysis.py` - Interference computation and energy analysis at lattice nodes
- `/app/runtime/topology_resolver.py` - Path enumeration through the directed lattice graph
- `/app/runtime/signal_filter.py` - Frequency-domain bandpass filtering at each node
- `/app/runtime/calibration.py` - Temporal quantization and alignment of signal arrivals
- `/app/runtime/aggregator.py` - Result collection and report generation
- `/app/runtime/pipeline.py` - Main orchestration pipeline
- `/app/runtime/config.ini` - Simulation parameters
- `/app/runtime/data/topology.json` - Lattice topology definition (7 nodes, weighted directed edges)
- `/app/runtime/data/trace_*.json` - Signal injection traces at various source nodes

## Output Schema

The pipeline writes a JSON synthesis report to `/app/runtime/output/synthesis_report.json` with the following structure:

```json
{
  "node_energies": { "<node_id>": <float>, ... },
  "propagation_delays": { "<src>-><dst>": <float>, ... },
  "interference_magnitudes": { "<node_id>": <float>, ... },
  "interference_phases": { "<node_id>": <float>, ... },
  "total_paths_found": <int>,
  "resonance_detected": [<int>, ...]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `node_energies` | object (string -> float) | Windowed RMS energy level at each node (keys are node IDs as strings: "0" through "6") |
| `propagation_delays` | object (string -> float) | Minimum propagation delay in seconds for each source-to-destination pair (keys formatted as `"<src>-><dst>"`, e.g., `"0->6"`) |
| `interference_magnitudes` | object (string -> float) | Peak phasor interference magnitude at each node where multiple signals converge |
| `interference_phases` | object (string -> float) | Phase angle in radians of the peak interference resultant at each node |
| `total_paths_found` | integer | Total number of simple paths enumerated across all source-target pairs |
| `resonance_detected` | array of integers | List of node IDs (as integers) where energy exceeds the configured `energy_threshold` |

## Expected Behavior

When the system is functioning correctly, the synthesis report should satisfy all of the following:

**Path Enumeration:**
- The lattice topology contains 14 distinct simple paths across all source-target pairs
- The DFS-based path finder must enumerate all valid non-repeating paths up to `max_hops` length

**Propagation Delays:**
- Minimum delay from node 0 to node 6: 0.006 seconds (via the 0->1->6 path)
- Minimum delay from node 3 to node 6: 0.007 seconds
- Minimum delay from node 5 to node 6: 0.003 seconds (direct 5->6 edge)

**Node Energies (windowed RMS):**
- Node 0 (source injection only): approximately 0.36
- Node 1: approximately 0.47
- Node 2 (major transit hub): approximately 0.85
- Node 3 (high-amplitude source): approximately 1.09
- Node 4 (multi-path receiver): approximately 0.36
- Node 5 (source + transit): approximately 1.13
- Node 6 (final destination): approximately 0.75

**Interference Patterns:**
- All 7 nodes should show non-zero interference magnitudes when multiple signal paths converge
- Node 2 receives signals from multiple sources and should exhibit strong interference (magnitude near 2.75)
- Node 5 interference magnitude should be approximately 1.8
- Node 6 (collecting all paths) should show interference magnitude near 1.12
- Node 4 interference should be approximately 0.87
- Node 1 interference should be approximately 0.70
- Node 3 interference magnitude should be approximately 2.8

**Resonance Detection:**
- With the configured `energy_threshold` of 0.15, all 7 nodes should be detected as resonant when path enumeration and energy computation are correct
- Node 4 is particularly sensitive: its energy only exceeds the threshold when all paths reaching it are properly enumerated

## Problem Description

The pipeline runs to completion and produces a synthesis report, but the computed values are incorrect. Operators have observed that the reported energy distributions, interference patterns, and path counts do not match the expected values described above. The anomalies appear to involve subtle numerical issues in the signal processing chain rather than outright crashes or obvious logic errors.

## Task

Identify and fix the issues causing incorrect synthesis report values. The repaired system should produce a synthesis report matching the expected behavior described above.

## Running the Pipeline

```bash
cd /app
python3 -m runtime.pipeline
```

The output will be written to `/app/runtime/output/synthesis_report.json`.
