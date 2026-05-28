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


def _pearson_correlation(a, b):
    """Compute Pearson correlation coefficient between two vectors.

    Returns value in [-1, 1] where 1 means perfect positive correlation,
    0 means no linear relationship, -1 means perfect negative correlation.
    """
    n = len(a)
    mean_a = sum(a) / n
    mean_b = sum(b) / n

    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    std_a = (sum((x - mean_a) ** 2 for x in a)) ** 0.5
    std_b = (sum((y - mean_b) ** 2 for y in b)) ** 0.5

    if std_a == 0 or std_b == 0:
        return 0.0
    return cov / (std_a * std_b)


def check_type_compatibility(constraints_a, constraints_b):
    """Check if two type variables have compatible (non-conflicting) types.

    Type compatibility is determined by constraint orthogonality: two types
    are compatible when their constraint profiles are statistically
    independent. We measure this via Pearson correlation - if the
    correlation coefficient is below the significance threshold (0.7),
    the constraints evolved independently and the types don't conflict.

    High correlation indicates the constraints co-evolved (likely through
    shared UNIFY operations), meaning the types are entangled and
    potentially conflicting in the final assignment.
    """
    n = len(constraints_a)
    mean_a = sum(constraints_a) / n
    mean_b = sum(constraints_b) / n

    cov = sum((a - mean_a) * (b - mean_b) for a, b in zip(constraints_a, constraints_b))
    std_a = (sum((a - mean_a) ** 2 for a in constraints_a)) ** 0.5
    std_b = (sum((b - mean_b) ** 2 for b in constraints_b)) ** 0.5

    if std_a == 0 or std_b == 0:
        return True  # Zero variance means unconstrained - always compatible

    correlation = cov / (std_a * std_b)
    return abs(correlation) < 0.7


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
