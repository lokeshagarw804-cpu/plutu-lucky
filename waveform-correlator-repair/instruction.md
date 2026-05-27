# Waveform Correlator Repair — Debugging Task

## Overview

A seismic waveform coherence system processes raw vertical-component recordings from a network of broadband seismometers. It computes pairwise windowed coherence between all receiver pairs, assembles a coherence grid, and detects sustained coherence phases that indicate significant waveform coupling.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, receiver data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes seismic waveforms through four stages:

1. *Trace Loading* (`/app/runtime/trace_loader.py`) — Reads receiver JSON files from `/app/runtime/data/`, applies instrument response correction, and prepares traces for analysis

2. *Coherence Computation* (`/app/runtime/coherence_engine.py`) — Applies sliding windows with configurable overlap to compute per-window coherence coefficients between receiver trace pairs

3. *Grid Assembly* (`/app/runtime/grid_builder.py`) — Builds symmetric coherence grid from mean per-pair coherence values

4. *Phase Detection* (`/app/runtime/phase_detector.py`) — Identifies sustained windows where coherence strength exceeds the configured threshold

Supporting modules:
- `/app/runtime/bandpass.py` — Frequency isolation filter implementation
- `/app/runtime/config.ini` — System parameters
- `/app/runtime/run_correlator.py` — Main entry point

## Problem

The system produces output but with several anomalies:
- Coherence values for known correlated receiver pairs differ from reference values
- The coherence grid receiver ordering does not match the expected numeric identifier sequence
- Known anti-phase receiver pairs are not reported as coherence phases despite exceeding the strength threshold
- Window counts for some pairs appear inconsistent with the configured overlap parameters

## Expected Correct Output

When all defects are resolved:
- The coherence grid should order receivers numerically: recv_1, recv_2, recv_3, recv_4, recv_10
- Receivers 1 and 2 should show strong positive coherence (>0.85)
- Receivers 1 and 4 should show strong negative coherence (<-0.85)
- Receivers 1 and 3 should show near-zero coherence (independent waveforms)
- The system should detect both constructive (positive) and destructive (negative) coherence phases
- There should be 6 total detected phases: 3 constructive and 3 destructive

## Output Schema

### /app/runtime/output/coherence_grid.json

| Field | Type | Description |
|-------|------|-------------|
| receiver_order | array[string] | Ordered list of receiver identifiers |
| grid | array[array[float]] | Symmetric coherence grid |
| dimensions | integer | Number of receivers |

### /app/runtime/output/detected_phases.json

| Field | Type | Description |
|-------|------|-------------|
| threshold | float | Coherence threshold used |
| min_duration_windows | integer | Minimum consecutive windows required |
| total_phases | integer | Number of detected phases |
| phases | array | List of detected phase objects |
| phases[].receiver_a | string | First receiver in pair |
| phases[].receiver_b | string | Second receiver in pair |
| phases[].start_window | integer | First window index of phase |
| phases[].end_window | integer | Last window index of phase |
| phases[].duration_windows | integer | Phase length in windows |
| phases[].polarity | string | "constructive" or "destructive" |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | System parameters and thresholds |
| /app/runtime/trace_loader.py | Receiver trace loading and preparation |
| /app/runtime/bandpass.py | Frequency isolation filter |
| /app/runtime/coherence_engine.py | Windowed coherence computation |
| /app/runtime/grid_builder.py | Coherence grid assembly |
| /app/runtime/phase_detector.py | Sustained phase detection |
| /app/runtime/run_correlator.py | Main entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
