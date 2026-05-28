"""
Report Writer
==============
Produces the final inference report including type compatibility
classification, resolution priority ordering, and system digest.
"""
import hashlib
import json

from type_analyzer import find_compatible_pairs, rank_type_priority


def compute_digest(type_ids, constraints):
    """Compute a 16-character hex digest of the constraint state."""
    sorted_ids = sorted(type_ids)
    parts = []
    for tid in sorted_ids:
        vec_str = ','.join(str(v) for v in constraints[tid])
        parts.append(f"{tid}:{vec_str}")
    canonical = '|'.join(parts)
    return hashlib.md5(canonical.encode()).hexdigest()[:16]


def generate_report(type_ids, constraints, events, output_path):
    """Generate the inference report JSON file."""
    compatible_pairs = find_compatible_pairs(type_ids, constraints)
    priority_order = rank_type_priority(type_ids, constraints, events)
    digest = compute_digest(type_ids, constraints)

    report = {
        'compatible_pairs': compatible_pairs,
        'compatible_pair_count': len(compatible_pairs),
        'priority_order': priority_order,
        'digest': digest
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report
