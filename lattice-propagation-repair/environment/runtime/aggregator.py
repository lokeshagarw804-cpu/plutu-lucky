# PLUTU-LUCKY-CANARY
"""Result aggregation module for lattice propagation synthesis reports.

Collects per-node energy levels, propagation delays, interference
metrics, and resonance detection into a unified synthesis report.
"""

import json
import os


def aggregate_results(node_energies, propagation_delays, interference_results,
                      total_paths, resonant_nodes):
    """Aggregate all analysis results into the synthesis report structure.

    Args:
        node_energies: Dict mapping node_id (str) to energy value.
        propagation_delays: Dict mapping path_key (str) to delay in seconds.
        interference_results: Dict mapping node_id (str) to interference dict.
        total_paths: Total number of paths found across all source-dest pairs.
        resonant_nodes: List of node IDs where resonance was detected.

    Returns:
        Complete synthesis report dict.
    """
    interference_magnitudes = {}
    interference_phases = {}

    for node_id, result in interference_results.items():
        interference_magnitudes[node_id] = result['magnitude']
        interference_phases[node_id] = result['phase']

    report = {
        'node_energies': node_energies,
        'propagation_delays': propagation_delays,
        'interference_magnitudes': interference_magnitudes,
        'interference_phases': interference_phases,
        'total_paths_found': total_paths,
        'resonance_detected': resonant_nodes
    }

    return report


def write_report(report, output_path):
    """Write synthesis report to JSON file.

    Creates output directory if it does not exist.

    Args:
        report: Synthesis report dict.
        output_path: Full path for the output JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)


def merge_node_energies(energy_contributions):
    """Merge energy contributions from multiple traces at each node.

    Sums energy contributions from different signal sources that
    propagate through the same node.

    Args:
        energy_contributions: List of dicts, each mapping node_id to energy.

    Returns:
        Merged dict mapping node_id to total energy.
    """
    merged = {}
    for contribution in energy_contributions:
        for node_id, energy in contribution.items():
            if node_id in merged:
                merged[node_id] += energy
            else:
                merged[node_id] = energy
    return merged


def format_delay_key(source, target):
    """Create a standardized key for the propagation delays dict.

    Args:
        source: Source node ID.
        target: Target node ID.

    Returns:
        Formatted string key like '0->6'.
    """
    return f"{source}->{target}"
