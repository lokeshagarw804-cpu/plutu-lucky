"""
Particle Collision Repair Script
=================================
Fixes the collision simulation by correcting three issues:

1. collision_engine.py: ABSORB events must increment own momentum
   component after merging neighbor state (collision thrust).

2. interaction_analyzer.py: Causal independence must use vector
   incomparability (neither dominates) not vector equality.

3. interaction_analyzer.py: Evolution priority must sort by total
   vector sum (accumulated energy) not last event timestamp.

After patching, re-runs the simulation to produce corrected output.
"""
import os
import subprocess
import sys


def get_runtime_dir():
    """Determine the runtime directory based on execution context."""
    # Check if running in Docker container
    if os.path.isdir('/app/runtime'):
        return '/app/runtime'
    # Running locally - relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '..', 'runtime')


RUNTIME_DIR = get_runtime_dir()


def fix_collision_engine():
    """Fix Bug 1: Add own-component increment after ABSORB merge."""
    filepath = os.path.join(RUNTIME_DIR, 'collision_engine.py')
    with open(filepath, 'r') as f:
        content = f.read()

    # The bug is that apply_absorb does not increment own component after merge.
    # We need to add self._momentum[self.particle_id] += 1 before self._event_count += 1
    old = """        for pid in self._particle_ids:
            if pid in neighbor_state:
                self._momentum[pid] = max(self._momentum[pid], neighbor_state[pid])
        self._event_count += 1"""

    new = """        for pid in self._particle_ids:
            if pid in neighbor_state:
                self._momentum[pid] = max(self._momentum[pid], neighbor_state[pid])
        self._momentum[self.particle_id] += 1
        self._event_count += 1"""

    content = content.replace(old, new)
    with open(filepath, 'w') as f:
        f.write(content)


def fix_interaction_analyzer():
    """Fix Bugs 2 and 3: independence check and priority sorting."""
    filepath = os.path.join(RUNTIME_DIR, 'interaction_analyzer.py')
    with open(filepath, 'r') as f:
        content = f.read()

    # Fix Bug 2: Replace equality check with incomparability check
    old_independence = """    return vector_leq(vec_a, vec_b) and vector_leq(vec_b, vec_a)"""
    new_independence = """    return not vector_dominates(vec_a, vec_b) and not vector_dominates(vec_b, vec_a)"""
    content = content.replace(old_independence, new_independence)

    # Fix Bug 3: Replace last-event-timestamp sorting with vector-sum sorting
    old_priority = """    last_event_step = {pid: 0 for pid in particles}
    for event in events:
        pid = event['particle_id']
        if pid in last_event_step:
            last_event_step[pid] = event['seq']

    # Sort by most recent event timestamp descending - particles in
    # active reaction zones get priority for evolution scheduling
    priority_order = sorted(particles, key=lambda p: last_event_step[p], reverse=True)
    return priority_order"""

    new_priority = """    # Sort by total momentum energy descending - particles with
    # highest accumulated energy represent the most active fronts
    priority_order = sorted(particles, key=lambda p: sum(vectors[p]), reverse=True)
    return priority_order"""

    content = content.replace(old_priority, new_priority)

    with open(filepath, 'w') as f:
        f.write(content)


def rerun_simulation():
    """Re-run the simulator to produce corrected output."""
    simulator_path = os.path.join(RUNTIME_DIR, 'simulator.py')
    subprocess.run([sys.executable, simulator_path], check=True)


if __name__ == '__main__':
    fix_collision_engine()
    fix_interaction_analyzer()
    rerun_simulation()
    print("Repair complete. Simulation output has been regenerated.")
