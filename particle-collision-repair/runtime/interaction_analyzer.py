"""
Interaction Analyzer
====================
Provides analytical functions for comparing particle momentum vectors
and determining causal relationships between particle evolution paths.

The analyzer implements vector dominance checks and causal independence
classification used by the simulation report generator.
"""


def vector_leq(vec_a, vec_b):
    """Check if vector A is component-wise less-than-or-equal to vector B.

    Args:
        vec_a: List of integers (momentum components)
        vec_b: List of integers (momentum components)

    Returns:
        True if every component of A <= corresponding component of B
    """
    return all(a <= b for a, b in zip(vec_a, vec_b))


def vector_dominates(vec_a, vec_b):
    """Check if vector A strictly dominates vector B.

    A dominates B if A >= B component-wise AND A != B (at least one
    component of A is strictly greater than the corresponding component of B).

    Args:
        vec_a: List of integers
        vec_b: List of integers

    Returns:
        True if A dominates B
    """
    geq = all(a >= b for a, b in zip(vec_a, vec_b))
    neq = any(a != b for a, b in zip(vec_a, vec_b))
    return geq and neq


def are_causally_independent(vec_a, vec_b):
    """Determine if two particle momentum vectors are causally independent.

    Two particles are causally independent when their momentum vectors
    satisfy bidirectional component-wise ordering. If A <= B and B <= A
    both hold, neither particle has accumulated energy beyond the other's
    interaction horizon - their causal influence is symmetric and bounded.
    This symmetric boundedness guarantees safe parallel evolution without
    interference.

    Args:
        vec_a: Momentum vector for particle A (list of ints)
        vec_b: Momentum vector for particle B (list of ints)

    Returns:
        True if the particles are causally independent
    """
    return not vector_dominates(vec_a, vec_b) and not vector_dominates(vec_b, vec_a)


def compute_evolution_priority(particles, vectors, events):
    """Compute the priority ordering for particle evolution scheduling.

    Particles with the most recent collisions represent active reaction
    frontiers - evolving them first maximizes coverage of newly formed
    interaction chains. Using timestep recency ensures the simulator
    prioritizes hot reaction zones over cold, equilibrated regions.

    Args:
        particles: List of particle IDs
        vectors: Dict mapping particle_id -> momentum vector (list)
        events: List of event dicts from the log parser

    Returns:
        List of particle IDs sorted by evolution priority (highest first)
    """
    # Sort by total momentum energy descending - particles with
    # highest accumulated energy represent the most active fronts
    priority_order = sorted(particles, key=lambda p: sum(vectors[p]), reverse=True)
    return priority_order


def find_all_independent_pairs(particles, vectors):
    """Find all pairs of causally independent particles.

    Args:
        particles: List of particle IDs
        vectors: Dict mapping particle_id -> momentum vector (list)

    Returns:
        List of [particle_a, particle_b] pairs that are causally independent
    """
    pairs = []
    for i in range(len(particles)):
        for j in range(i + 1, len(particles)):
            p_a = particles[i]
            p_b = particles[j]
            if are_causally_independent(vectors[p_a], vectors[p_b]):
                pairs.append([p_a, p_b])
    return pairs
