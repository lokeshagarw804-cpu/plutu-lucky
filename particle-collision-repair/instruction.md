# Particle Collision Simulation -- Debugging Task

## Overview

A particle collision simulation processes event traces for 7 particles (alpha, beta, gamma, delta, epsilon, zeta, eta) through a momentum tracking engine, performs causal analysis on the resulting state vectors, and produces a structured report. The system reads collision events from a data file and maintains a per-particle momentum vector with one component per particle in the simulation.

## System Environment

- **Language**: Python 3.11
- **Runtime**: /app/runtime/ (source modules, collision trace data, output)
- **Global system-wide tooling**: uv and pytest are available
- **Dependencies**: stdlib-only (no external packages)

## Architecture

The system processes collision events through four stages:

1. **Parsing** (`/app/runtime/log_parser.py`) -- Reads the arrow-separated collision trace from `/app/runtime/collision_log.dat`

2. **Engine** (`/app/runtime/collision_engine.py`) -- Applies DRIFT, SCATTER, and ABSORB events to each particle's momentum vector

3. **Analysis** (`/app/runtime/interaction_analyzer.py`) -- Determines causal independence between particle pairs and computes evolution priority ordering

4. **Reporting** (`/app/runtime/simulation_report.py`) -- Generates the collision report with pair classifications, priority order, and state digest

5. **Orchestration** (`/app/runtime/simulator.py`) -- Drives the full pipeline end-to-end

## Problem

The system produces output but with several anomalies:

- Alpha particle's self-momentum component shows 12, but given its 9 events (4 DRIFT, 2 SCATTER, 2 ABSORB, 1 DRIFT) starting from BASE_ENERGY=3, the expected value should be higher
- The causal independence analysis finds 0 independent pairs, but with 7 particles that each have unique peak components, more pairs should qualify
- The evolution priority order appears to be sorted by event recency rather than by accumulated momentum strength
- The report digest does not match the expected fingerprint for a correctly functioning simulation

## Correct Files (no bugs)

- `/app/runtime/log_parser.py`
- `/app/runtime/simulator.py`

## Files Containing Bugs

- `/app/runtime/collision_engine.py`
- `/app/runtime/interaction_analyzer.py`
- `/app/runtime/simulation_report.py` (depends on analyzer output)

## Output Schema

### /app/runtime/simulation_state.jsonl

One JSON object per line, one line per particle:

| Field | Type | Description |
|-------|------|-------------|
| particle_id | string | Particle identifier |
| momentum_vector | object | Maps particle_id to integer momentum value |
| total_energy | integer | Sum of all momentum components |
| event_count | integer | Number of events processed |

### /app/runtime/collision_report.json

| Field | Type | Description |
|-------|------|-------------|
| independent_pairs | array | List of [particle_a, particle_b] causally independent pairs |
| independent_pair_count | integer | Number of independent pairs found |
| priority_order | array | Particle IDs sorted by evolution priority (highest first) |
| digest | string | 16-character hex MD5 fingerprint of canonical state |

## Running the Simulation

```bash
python3 /app/runtime/simulator.py
```

## Running Tests

```bash
pytest /tests/test_particle_collision.py -v
```

## Key Facts

- BASE_ENERGY = 3 (initial value for all vector components)
- DRIFT adds 1 to the particle's own component
- SCATTER adds 2 to the particle's own component
- ABSORB takes component-wise maximum from a neighbor state snapshot
- 7 particles, 45 total events in the collision log
- Alpha has the most events (9); others have 5-7
