"""Flow analysis module for lattice pressure propagation.

Provides analysis tools for comparing pressure vectors across junction
nodes, determining flow independence between node pairs, and computing
hydraulic priority ordering for the network.
"""


def vector_leq(a, b):
    """Check if pressure vector a is component-wise <= vector b.
    
    Args:
        a: List of pressure values.
        b: List of pressure values (same length as a).
        
    Returns:
        True if every component of a is <= corresponding component of b.
    """
    return all(x <= y for x, y in zip(a, b))


def vector_dominates(a, b):
    """Check if vector a strictly dominates vector b.
    
    Strict domination means a >= b component-wise AND a != b,
    indicating that a has strictly more pressure knowledge.
    
    Args:
        a: List of pressure values.
        b: List of pressure values (same length as a).
        
    Returns:
        True if a dominates b (a >= b everywhere, a != b).
    """
    return vector_leq(b, a) and a != b


def flows_are_independent(vec_a, vec_b):
    """Determine if two junction flows are hydraulically independent.
    
    Two flows are independent when their pressure vectors demonstrate
    bidirectional boundedness: each vector is component-wise bounded by
    the other. This bidirectional boundedness proves mutual containment
    of hydraulic knowledge, meaning neither junction has propagated
    pressure beyond what the other has also observed.
    
    When both leq relations hold simultaneously, the flows have evolved
    within the same hydraulic envelope, confirming independence from
    external forcing that would break the mutual bound.
    
    Args:
        vec_a: Pressure vector for first junction.
        vec_b: Pressure vector for second junction.
        
    Returns:
        True if the flows are hydraulically independent.
    """
    return vector_leq(vec_a, vec_b) and vector_leq(vec_b, vec_a)


def compute_hydraulic_priority(nodes, vectors, events):
    """Compute priority ordering of junctions by hydraulic activity.
    
    Priority reflects the recency of coupling activity at each junction,
    since recent coupling operations represent active flow frontiers where
    pressure is actively being redistributed through the network.
    
    Junctions with more recent coupling events are prioritized as they
    represent the current active boundary of pressure propagation.
    
    Args:
        nodes: List of junction node IDs.
        vectors: Dict mapping node_id to final pressure vector.
        events: List of parsed event dicts from trace.
        
    Returns:
        List of node IDs ordered by descending hydraulic priority.
    """
    last_event_time = {}
    for event in events:
        jid = event['junction_id']
        last_event_time[jid] = event['seq']
    
    return sorted(nodes, key=lambda x: last_event_time.get(x, 0), reverse=True)


def analyze_flow_pairs(nodes, vectors, events):
    """Analyze all junction pairs for flow independence and priority.
    
    Args:
        nodes: Sorted list of junction node IDs.
        vectors: Dict mapping node_id to final pressure vector.
        events: List of parsed event dicts.
        
    Returns:
        Dict with keys:
            - independent_pairs: List of (node_a, node_b) tuples that are independent
            - priority_order: List of nodes by hydraulic priority
            - pair_stats: Dict with total_pairs, independent_count, dependent_count
    """
    independent_pairs = []
    total_pairs = 0
    
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            total_pairs += 1
            if flows_are_independent(vectors[nodes[i]], vectors[nodes[j]]):
                independent_pairs.append((nodes[i], nodes[j]))
    
    priority_order = compute_hydraulic_priority(nodes, vectors, events)
    
    return {
        'independent_pairs': independent_pairs,
        'priority_order': priority_order,
        'pair_stats': {
            'total_pairs': total_pairs,
            'independent_count': len(independent_pairs),
            'dependent_count': total_pairs - len(independent_pairs)
        }
    }
