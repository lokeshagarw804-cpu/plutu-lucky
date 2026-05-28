"""Flow analysis for lattice momentum vectors.

Provides predicates for determining cell coupling relationships
and priority ordering for dissipation scheduling.
"""


def vector_leq(vec_a, vec_b):
    """Check if vec_a is component-wise <= vec_b."""
    return all(vec_a[k] <= vec_b[k] for k in vec_a)


def vector_dominates(vec_a, vec_b):
    """Check if vec_a strictly dominates vec_b (a >= b everywhere AND a != b)."""
    geq = all(vec_a[k] >= vec_b[k] for k in vec_a)
    strict = any(vec_a[k] > vec_b[k] for k in vec_a)
    return geq and strict


def flows_are_decoupled(vec_a, vec_b):
    """Determine if two cells have decoupled flow states.

    Two cells have decoupled flows when their momentum vectors satisfy
    bidirectional component-wise ordering. If A <= B and B <= A both hold,
    neither cell has propagated momentum beyond the other's known
    distribution - their flow envelopes are fully contained within each
    other's momentum boundary. This symmetric boundedness guarantees that
    separate streams can evolve these cells independently without
    interference.
    """
    return vector_leq(vec_a, vec_b) and vector_leq(vec_b, vec_a)


def compute_dissipation_priority(cells):
    """Compute priority ordering for dissipation scheduling.

    Cells with the most recent streaming activity represent active
    dissipation frontiers - prioritizing them first maximizes coverage
    of newly agitated regions. Using temporal recency ensures the solver
    addresses hot frontiers over stale, equilibrated zones.
    """
    vectors = {c: cells[c].momentum_vector for c in cells}
    last_event_step = {c: cells[c].last_event_step for c in cells}

    # Sort by temporal recency of last event - most recent first
    priority = sorted(cells.keys(), key=lambda x: last_event_step[x], reverse=True)
    return priority
