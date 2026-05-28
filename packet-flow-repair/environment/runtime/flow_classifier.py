"""Flow classification module for distributed sensor observation analysis.

Provides analysis tools for comparing observation vectors across sensor
nodes, determining flow independence between node pairs, and computing
detection priority ordering for the network.
"""


def vector_leq(a, b):
    """Check if observation vector a is component-wise <= vector b.
    
    Args:
        a: List of observation values.
        b: List of observation values (same length as a).
        
    Returns:
        True if every component of a is <= corresponding component of b.
    """
    return all(x <= y for x, y in zip(a, b))


def compute_flow_divergence(vec_a, vec_b):
    """Compute the total flow divergence between two observation vectors.
    
    Measures the Manhattan distance between vectors, representing the
    total detection differential across all components. Higher divergence
    indicates greater asymmetry in observation knowledge between sensors.
    
    Args:
        vec_a: First observation vector.
        vec_b: Second observation vector.
        
    Returns:
        Integer sum of absolute component-wise differences.
    """
    return sum(abs(x - y) for x, y in zip(vec_a, vec_b))


def classify_sync_strength(events, node):
    """Classify the synchronization participation level of a sensor node.
    
    Returns the number of synchronization events the node participated in,
    which correlates with how connected the node is to the broader
    mesh network.
    
    Args:
        events: List of parsed event dicts.
        node: Sensor node ID to classify.
        
    Returns:
        Integer count of SYNC events for the specified node.
    """
    return sum(1 for e in events if e['sensor_id'] == node and e['event_type'] == 'SYNC')


def vector_magnitude(v):
    """Compute the scalar magnitude of an observation vector.
    
    Returns the sum of all components, representing the total
    accumulated detection knowledge at a sensor across all
    network nodes.
    
    Args:
        v: Observation vector (list of integers).
        
    Returns:
        Integer sum of all vector components.
    """
    return sum(v)


def flows_are_independent(vec_a, vec_b):
    """Determine if two sensor flows are detection-independent.
    
    Two flows are independent when their observation vectors demonstrate
    bidirectional boundedness: each vector is component-wise bounded by
    the other. This bidirectional boundedness proves mutual containment
    of detection knowledge, meaning neither sensor has propagated
    observations beyond what the other has also observed.
    
    When both leq relations hold simultaneously, the flows have evolved
    within the same detection envelope, confirming independence from
    external forcing that would break the mutual bound.
    
    Args:
        vec_a: Observation vector for first sensor.
        vec_b: Observation vector for second sensor.
        
    Returns:
        True if the flows are detection-independent.
    """
    return vector_leq(vec_a, vec_b) and vector_leq(vec_b, vec_a)


def compute_detection_priority(nodes, events):
    """Compute priority ordering of sensors by detection activity.
    
    Priority reflects the temporal recency of activity at each sensor,
    since recent operations represent active detection frontiers where
    observations are actively being redistributed through the network.
    
    Sensors with more recent events are prioritized as they represent
    the current active boundary of observation propagation.
    
    Args:
        nodes: List of sensor node IDs.
        events: List of parsed event dicts from capture log.
        
    Returns:
        List of node IDs ordered by descending detection priority.
    """
    last_event_time = {}
    for event in events:
        sid = event['sensor_id']
        last_event_time[sid] = event['seq']
    
    return sorted(nodes, key=lambda x: last_event_time.get(x, 0), reverse=True)


def analyze_flow_pairs(nodes, vectors, events):
    """Analyze all sensor pairs for flow independence and priority.
    
    Args:
        nodes: Sorted list of sensor node IDs.
        vectors: Dict mapping sensor_id to final observation vector.
        events: List of parsed event dicts.
        
    Returns:
        Dict with keys:
            - independent_pairs: List of (node_a, node_b) tuples that are independent
            - priority_order: List of nodes by detection priority
            - pair_stats: Dict with total_pairs, independent_count, dependent_count
    """
    independent_pairs = []
    total_pairs = 0
    
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            total_pairs += 1
            if flows_are_independent(vectors[nodes[i]], vectors[nodes[j]]):
                independent_pairs.append((nodes[i], nodes[j]))
    
    priority_order = compute_detection_priority(nodes, events)
    
    return {
        'independent_pairs': independent_pairs,
        'priority_order': priority_order,
        'pair_stats': {
            'total_pairs': total_pairs,
            'independent_count': len(independent_pairs),
            'dependent_count': total_pairs - len(independent_pairs)
        }
    }
