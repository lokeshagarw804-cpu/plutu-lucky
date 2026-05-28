"""Lattice Boltzmann simulation orchestrator.

Coordinates the full simulation pipeline: parse propagation log,
build momentum state, analyze flows, and generate reports.
"""
import json
import os
import hashlib

from parser import parse_log
from momentum_engine import build_lattice_state
from flow_analyzer import compute_dissipation_priority
from report_writer import generate_report


def compute_digest(state_path, report_path):
    """Compute simulation digest from output files."""
    h = hashlib.md5()
    with open(state_path, 'r') as f:
        h.update(f.read().encode())
    with open(report_path, 'r') as f:
        h.update(f.read().encode())
    return h.hexdigest()[:16]


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_dir, 'propagation_log.dat')
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    state_path = os.path.join(output_dir, 'lattice_state.jsonl')
    report_path = os.path.join(output_dir, 'flow_report.json')

    # Parse log
    events = parse_log(log_path)

    # Build momentum state
    cells = build_lattice_state(events)

    # Write state file (one JSON line per cell, sorted)
    with open(state_path, 'w') as f:
        for cell_id in sorted(cells.keys()):
            cell = cells[cell_id]
            record = {
                'cell_id': cell_id,
                'momentum_vector': cell.momentum_vector,
                'total_events': cell.event_count
            }
            f.write(json.dumps(record) + '\n')

    # Generate flow report
    report = generate_report(cells, report_path)

    # Compute and append digest
    digest = compute_digest(state_path, report_path)
    report['simulation_digest'] = digest
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    return digest


if __name__ == '__main__':
    digest = main()
    print(f"Simulation complete. Digest: {digest}")
