"""
Synthesis Output
=================
Produces the final synthesis report including signal isolation
classification, propagation priority ordering, and simulation digest.
"""
import hashlib
import json

from lattice_analysis import find_isolated_pairs, rank_propagation_fronts


def compute_digest(nodes, depths):
    """Compute a 16-character hex digest of the propagation state."""
    sorted_nodes = sorted(nodes)
    parts = []
    for nid in sorted_nodes:
        vec_str = ','.join(str(v) for v in depths[nid])
        parts.append(f"{nid}:{vec_str}")
    canonical = '|'.join(parts)
    return hashlib.md5(canonical.encode()).hexdigest()[:16]


def generate_report(nodes, depths, events, output_path):
    """Generate the synthesis report JSON file."""
    isolated_pairs = find_isolated_pairs(nodes, depths)
    priority_order = rank_propagation_fronts(nodes, depths, events)
    digest = compute_digest(nodes, depths)

    report = {
        'isolated_pairs': isolated_pairs,
        'isolated_pair_count': len(isolated_pairs),
        'priority_order': priority_order,
        'digest': digest
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report
