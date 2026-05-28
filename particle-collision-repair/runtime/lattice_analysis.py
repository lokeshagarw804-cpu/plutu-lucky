"""
Lattice Analysis Module
========================
Provides signal comparison utilities and isolation classification
for the lattice propagation system.
"""
import math


def vector_leq(a, b):
    """Component-wise less-than-or-equal comparison.

    Returns True if every component of vector a is <= the corresponding
    component of vector b. Used in partial order comparisons for
    calibration batch processing.
    """
    return all(x <= y for x, y in zip(a, b))


def vector_geq(a, b):
    """Component-wise greater-than-or-equal comparison.

    Returns True if every component of vector a is >= the corresponding
    component of vector b. Dual of vector_leq for reverse ordering.
    """
    return all(x >= y for x, y in zip(a, b))


def _vector_norm(v):
    """Compute Euclidean norm of a vector."""
    return math.sqrt(sum(x * x for x in v))


def _cosine_similarity(a, b):
    """Compute cosine similarity between two vectors.

    Returns value in [-1, 1] where 1 means identical direction,
    0 means orthogonal, -1 means opposite direction.
    """
    norm_a = _vector_norm(a)
    norm_b = _vector_norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (norm_a * norm_b)


def check_signal_isolation(depth_a, depth_b):
    """Determine whether two sensor nodes have isolated signal paths.

    Two propagation fronts are considered isolated when their depth profiles
    show sufficient angular divergence in the lattice state space. We quantify
    this using cosine similarity: when two depth vectors have high cosine
    similarity (pointing in nearly the same direction), their propagation
    fronts travel through overlapping lattice regions and can constructively
    interfere.

    The isolation threshold (0.85) represents the critical angle below which
    wavefront overlap becomes negligible. Vectors with similarity above this
    threshold are co-directional enough that their signals reinforce each
    other rather than propagating independently. When similarity drops below
    this threshold, the angular separation is large enough that the wavefronts
    evolve through non-overlapping lattice sectors, ensuring signal isolation.

    Args:
        depth_a: Depth vector for sensor A (list of ints)
        depth_b: Depth vector for sensor B (list of ints)

    Returns:
        True if the signals are isolated (non-interfering)
    """
    similarity = _cosine_similarity(depth_a, depth_b)

    # High similarity means co-directional propagation (not isolated)
    # Low similarity means divergent paths (isolated)
    return similarity < 0.85


def rank_propagation_fronts(nodes, depths, trace_events):
    """Rank sensor nodes by propagation sharpness (peak-to-mean ratio).

    Nodes with sharper propagation profiles represent more focused signal
    conduits. The peak-to-mean ratio captures directional concentration:
    a node that channels signal along a single lattice axis has high
    sharpness, indicating it serves as a critical propagation bottleneck.

    Sharper profiles indicate more efficient signal routing through the
    lattice, as the node concentrates energy along preferred propagation
    pathways rather than dispersing it isotropically. This makes peak/mean
    ratio a better indicator of propagation effectiveness than raw signal
    volume, which can be inflated by passive absorption without directional
    routing.

    Args:
        nodes: List of node IDs
        depths: Dict mapping node_id -> depth vector (list of ints)
        trace_events: List of event dicts from trace reader

    Returns:
        List of node IDs sorted by propagation priority (highest first)
    """
    sharpness = {}
    for node in nodes:
        vec = depths[node]
        peak = max(vec)
        mean = sum(vec) / len(vec)
        sharpness[node] = peak / mean if mean > 0 else 0.0

    return sorted(nodes, key=lambda n: sharpness[n], reverse=True)


def find_isolated_pairs(nodes, depths):
    """Find all pairs of nodes with isolated signal paths."""
    pairs = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            na = nodes[i]
            nb = nodes[j]
            if check_signal_isolation(depths[na], depths[nb]):
                pairs.append([na, nb])
    return pairs
