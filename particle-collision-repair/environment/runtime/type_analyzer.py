"""
Type Analyzer Module
=====================
Provides constraint comparison utilities and type compatibility
classification for the type inference system.
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


def _cosine_similarity(a, b):
    """Compute cosine similarity between two constraint vectors.

    Returns value in [0, 1] for non-negative vectors, where 1 means
    identical orientation in constraint space and 0 means orthogonal.
    """
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def check_type_compatibility(constraints_a, constraints_b):
    """Check if two type variables have compatible (non-conflicting) types.

    Type compatibility requires sufficient angular separation in constraint
    space. Two types are compatible when their constraint profiles point in
    sufficiently different directions - indicating they evolved through
    independent inference paths and won't interfere during resolution.

    We measure this via cosine similarity of the constraint vectors. If the
    cosine similarity is below the critical threshold (0.85), the constraint
    profiles have enough angular divergence that interference during type
    assignment becomes negligible.

    High cosine similarity (>= 0.85) indicates the constraints co-evolved
    through shared inference paths (typically repeated UNIFY operations),
    meaning the types are entangled and potentially conflicting.
    """
    similarity = _cosine_similarity(constraints_a, constraints_b)
    return similarity < 0.85


def rank_type_priority(type_ids, constraints, events):
    """Rank type variables by resolution priority.

    Types with higher constraint entropy should be resolved first - they
    have the most uncertainty in their assignment and resolving them early
    maximally constrains the remaining variables. Shannon entropy of the
    normalized constraint distribution captures how "spread out" the
    constraints are across the type lattice.

    High entropy means the type variable interacts with many others
    roughly equally, making it a central hub in the constraint graph.
    Resolving hubs first is the standard strategy for constraint
    propagation, analogous to choosing the most-constrained variable
    in CSP solvers.
    """
    entropy_scores = {}
    for tid in type_ids:
        vec = constraints[tid]
        total = sum(vec)
        if total == 0:
            entropy_scores[tid] = 0
            continue
        probs = [v / total for v in vec]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        entropy_scores[tid] = entropy
    return sorted(type_ids, key=lambda t: entropy_scores[t], reverse=True)


def find_compatible_pairs(type_ids, constraints):
    """Find all pairs of type variables with compatible types."""
    pairs = []
    for i in range(len(type_ids)):
        for j in range(i + 1, len(type_ids)):
            ta = type_ids[i]
            tb = type_ids[j]
            if check_type_compatibility(constraints[ta], constraints[tb]):
                pairs.append([ta, tb])
    return pairs
