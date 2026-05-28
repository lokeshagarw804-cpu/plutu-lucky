"""
Simulation Report Generator
============================
Produces the final collision report including causal independence
classification, evolution priority ordering, and simulation digest.
"""
import hashlib
import json

from interaction_analyzer import find_all_independent_pairs, compute_evolution_priority


def compute_digest(particles, vectors):
    """Compute a 16-character hex digest of the simulation state.

    Creates a canonical string representation of all particle vectors
    and hashes it to produce a compact fingerprint.

    Args:
        particles: List of particle IDs (sorted)
        vectors: Dict mapping particle_id -> momentum vector (list)

    Returns:
        16-character hexadecimal digest string
    """
    sorted_particles = sorted(particles)
    parts = []
    for pid in sorted_particles:
        vec_str = ','.join(str(v) for v in vectors[pid])
        parts.append(f"{pid}:{vec_str}")
    canonical = '|'.join(parts)
    return hashlib.md5(canonical.encode()).hexdigest()[:16]


def generate_report(particles, vectors, events, output_path):
    """Generate the collision report JSON file.

    Args:
        particles: List of particle IDs
        vectors: Dict mapping particle_id -> momentum vector (list)
        events: List of event dicts
        output_path: Path to write the report JSON
    """
    independent_pairs = find_all_independent_pairs(particles, vectors)
    priority_order = compute_evolution_priority(particles, vectors, events)
    digest = compute_digest(particles, vectors)

    report = {
        'independent_pairs': independent_pairs,
        'independent_pair_count': len(independent_pairs),
        'priority_order': priority_order,
        'digest': digest
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report
