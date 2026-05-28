#!/usr/bin/env python3
"""Repair script for lattice Boltzmann momentum simulation.

Corrects momentum propagation calculations and flow analysis
logic to produce accurate simulation results.
"""
import sys
import os


def patch_momentum_engine():
    """Fix collision handling in momentum engine.

    The collision phase must account for the cell's participation
    in the momentum exchange - each collision event contributes
    a unit increment to the cell's own momentum component.
    """
    path = "/app/runtime/momentum_engine.py"
    with open(path, 'r') as f:
        content = f.read()

    content = content.replace(
        "        # The collision synchronizes knowledge only - no self-increment occurs\n"
        "        # because the cell is not actively streaming during a collision phase.\n"
        "        self._event_count += 1\n"
        "        self._last_event_step = step",
        "        # The collision synchronizes knowledge only - no self-increment occurs\n"
        "        # because the cell is not actively streaming during a collision phase.\n"
        "        self._momentum[self.cell_id] += 1\n"
        "        self._event_count += 1\n"
        "        self._last_event_step = step"
    )

    with open(path, 'w') as f:
        f.write(content)


def patch_flow_analyzer():
    """Fix flow decoupling predicate and dissipation priority.

    The decoupling check must use incomparability (neither dominates
    the other) rather than equality. The priority must reflect
    actual momentum magnitudes rather than temporal ordering.
    """
    path = "/app/runtime/flow_analyzer.py"
    with open(path, 'r') as f:
        content = f.read()

    content = content.replace(
        "    return vector_leq(vec_a, vec_b) and vector_leq(vec_b, vec_a)",
        "    return not vector_dominates(vec_a, vec_b) and not vector_dominates(vec_b, vec_a)"
    )

    content = content.replace(
        "    priority = sorted(cells.keys(), key=lambda x: last_event_step[x], reverse=True)",
        "    priority = sorted(cells.keys(), key=lambda x: sum(vectors[x].values()), reverse=True)"
    )

    with open(path, 'w') as f:
        f.write(content)


def main():
    patch_momentum_engine()
    patch_flow_analyzer()

    # Re-run simulation with corrected code
    sys.path.insert(0, '/app/runtime')
    # Clear cached modules to pick up patched files
    for key in list(sys.modules.keys()):
        if key in ('parser', 'momentum_engine', 'flow_analyzer',
                   'report_writer', 'orchestrator'):
            del sys.modules[key]
    from orchestrator import main as run_main
    run_main()


if __name__ == '__main__':
    main()
