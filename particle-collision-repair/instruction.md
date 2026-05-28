# Particle Collision Repair

## Overview

You are debugging a particle collision simulation system that tracks momentum vectors for 7 particles (alpha, beta, gamma, delta, epsilon, zeta, eta) as they process collision events from a trace log.

The simulation reads events from `collision_log.dat` and updates each particle's momentum vector. The system then analyzes causal relationships between particles and generates a report.

## System Architecture

- **collision_log.dat**: Arrow-separated event trace with DRIFT, SCATTER, and ABSORB events
- **log_parser.py**: Parses the collision log into structured event data (correct)
- **collision_engine.py**: Tracks momentum vectors per particle, applies event physics
- **interaction_analyzer.py**: Determines causal independence between particles and computes evolution priority
- **simulation_report.py**: Generates the final analysis report with independence pairs, priority ordering, and state digest
- **simulator.py**: Orchestrator that ties everything together (correct)

## Physics Model

Each particle maintains a momentum vector with one component per particle in the simulation, initialized to BASE_ENERGY (3).

Event types:
- **DRIFT**: Low-energy displacement, increments own component by 1
- **SCATTER**: High-energy deflection, increments own component by 2
- **ABSORB**: Absorbs momentum from interaction neighborhood via component-wise maximum transfer

## Causal Independence

Two particles are causally independent when neither particle's momentum vector dominates the other. A vector dominates another when it is component-wise greater-than-or-equal with at least one strict inequality.

## Evolution Priority

Particles should be prioritized for evolution scheduling based on their total accumulated energy (sum of momentum vector components).

## Your Task

The simulation has bugs that cause incorrect output. Find and fix them so that all 14 tests pass.

Run the simulation:
```bash
python3 /app/runtime/simulator.py
```

Run the tests:
```bash
pytest /tests/test_particle_collision.py -v
```

## Files You May Modify

- `/app/runtime/collision_engine.py`
- `/app/runtime/interaction_analyzer.py`

## Hints

- Pay attention to what ABSORB events should do to the particle's own momentum
- Consider the difference between vector equality and vector incomparability
- Think about what metric best represents a particle's importance for scheduling
