"""Flow report generation for lattice simulation.

Produces structured analysis of cell coupling relationships
and dissipation scheduling priorities.
"""
import json
from itertools import combinations
from flow_analyzer import flows_are_decoupled, compute_dissipation_priority


def generate_report(cells, output_path):
    """Generate flow analysis report.

    Classifies all cell pairs as coupled or decoupled based on their
    momentum vector relationships, and computes dissipation priority.
    """
    cell_ids = sorted(cells.keys())
    vectors = {c: cells[c].momentum_vector for c in cell_ids}

    decoupled_pairs = []
    coupled_pairs = []

    for id_a, id_b in combinations(cell_ids, 2):
        if flows_are_decoupled(vectors[id_a], vectors[id_b]):
            decoupled_pairs.append([id_a, id_b])
        else:
            coupled_pairs.append([id_a, id_b])

    priority = compute_dissipation_priority(cells)

    report = {
        'total_pairs': len(cell_ids) * (len(cell_ids) - 1) // 2,
        'decoupled_pairs': decoupled_pairs,
        'decoupled_count': len(decoupled_pairs),
        'coupled_pairs': coupled_pairs,
        'coupled_count': len(coupled_pairs),
        'dissipation_priority': priority,
        'priority_magnitudes': {c: sum(vectors[c].values()) for c in priority}
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report
