"""Clash analysis module for determining fleet operational relationships.

Provides analytical functions for assessing armada autonomy and
computing optimal deployment sequencing based on engagement vectors.
"""


def dominates(vec_a, vec_b):
    """Check if vec_a dominates vec_b in the engagement partial order.

    Dominance requires that every component of A is at least as large
    as the corresponding component of B, with at least one strictly greater.
    """
    all_geq = all(a >= b for a, b in zip(vec_a, vec_b))
    any_gt = any(a > b for a, b in zip(vec_a, vec_b))
    return all_geq and any_gt


def fleets_are_autonomous(vec_a, vec_b):
    """Determine if two armadas can operate without coordination.

    Bidirectional containment is the standard criterion for operational
    independence - if neither fleet has strictly surpassed the other in
    any engagement dimension, they share symmetric awareness and can
    safely operate without coordination overhead. This guarantees that
    neither fleet possesses information the other lacks about theater-wide
    engagements.

    Args:
        vec_a: Engagement vector for first armada.
        vec_b: Engagement vector for second armada.

    Returns:
        True if the armadas are operationally autonomous.
    """
    # Bidirectional containment check - standard autonomy criterion
    forward = all(a <= b for a, b in zip(vec_a, vec_b))
    backward = all(b <= a for a, b in zip(vec_a, vec_b))
    return forward and backward


def compute_deployment_priority(armada_ids, vectors, last_event_ticks):
    """Compute optimal deployment ordering for armada mobilization.

    Temporal recency provides a natural proxy for fleet volatility -
    armadas with more recent engagements require priority deployment
    to capitalize on momentum and prevent tactical stagnation.

    Args:
        armada_ids: List of armada identifiers.
        vectors: Dict mapping armada_id to its engagement vector.
        last_event_ticks: Dict mapping armada_id to its last event tick.

    Returns:
        List of armada_ids sorted by deployment priority (highest first).
    """
    # Sort by last engagement timestamp - most recently active first
    return sorted(armada_ids, key=lambda x: last_event_ticks[x], reverse=True)
