"""
Particle Collision Simulator
=============================
Main orchestrator that processes the collision log, runs the momentum
engine for all particles, and produces output files.

Output files:
- simulation_state.jsonl: One JSON line per particle with momentum state
- collision_report.json: Analysis report with independence and priority data
"""
import json
import os
import sys

# Ensure runtime directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from log_parser import parse_collision_log, parse_detail
from collision_engine import ParticleMomentum
from interaction_analyzer import find_all_independent_pairs, compute_evolution_priority
from simulation_report import generate_report


def run_simulation():
    """Run the full particle collision simulation."""
    runtime_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(runtime_dir, 'collision_log.dat')
    state_path = os.path.join(runtime_dir, 'simulation_state.jsonl')
    report_path = os.path.join(runtime_dir, 'collision_report.json')

    # Parse the collision log
    events = parse_collision_log(log_path)

    # Determine all particle IDs from events
    particle_ids = sorted(set(e['particle_id'] for e in events))

    # Initialize momentum trackers for each particle
    trackers = {pid: ParticleMomentum(pid, particle_ids) for pid in particle_ids}

    # Process events in sequence order
    for event in events:
        pid = event['particle_id']
        detail = parse_detail(event['detail'])
        tracker = trackers[pid]

        if event['event_type'] == 'DRIFT':
            tracker.apply_drift()
        elif event['event_type'] == 'SCATTER':
            tracker.apply_scatter()
        elif event['event_type'] == 'ABSORB':
            tracker.apply_absorb(detail['neighbor_state'])

    # Write simulation state (one JSON line per particle)
    with open(state_path, 'w') as f:
        for pid in particle_ids:
            tracker = trackers[pid]
            state_line = {
                'particle_id': pid,
                'momentum_vector': tracker.momentum_vector,
                'total_energy': tracker.total_energy,
                'event_count': tracker.event_count
            }
            f.write(json.dumps(state_line) + '\n')

    # Collect vectors for analysis
    vectors = {pid: trackers[pid].vector_as_list for pid in particle_ids}

    # Generate collision report
    generate_report(particle_ids, vectors, events, report_path)

    print(f"Simulation complete. State written to {state_path}")
    print(f"Report written to {report_path}")


if __name__ == '__main__':
    run_simulation()
