"""Report generation for distributed sensor network analysis results.

Produces the final analysis report including flow state summary,
independence classification, priority ordering, and verification digest.
"""
import hashlib
import json

from flow_classifier import (
    flows_are_independent,
    compute_flow_divergence,
    classify_sync_strength,
    vector_magnitude,
)


def generate_report(nodes, vectors, analysis_result, events):
    """Generate comprehensive flow analysis report.
    
    Args:
        nodes: Sorted list of sensor node IDs.
        vectors: Dict mapping sensor_id to final observation vector.
        analysis_result: Output from analyze_flow_pairs().
        events: List of parsed event dicts.
        
    Returns:
        Dict containing the full report structure.
    """
    # Build sensor summaries
    sensor_summaries = {}
    for node in nodes:
        vec = vectors[node]
        sensor_summaries[node] = {
            'observation_vector': vec,
            'vector_sum': vector_magnitude(vec),
            'max_component': max(vec),
            'event_count': sum(1 for e in events if e['sensor_id'] == node),
            'sync_strength': classify_sync_strength(events, node),
        }
    
    # Cross-validation: independently verify pair classifications
    cross_validation = {}
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            pair_key = f"{nodes[i]}:{nodes[j]}"
            cross_validation[pair_key] = {
                'independent': flows_are_independent(vectors[nodes[i]], vectors[nodes[j]]),
                'divergence': compute_flow_divergence(vectors[nodes[i]], vectors[nodes[j]]),
            }
    
    # Compute network-wide metrics
    magnitudes = {node: vector_magnitude(vectors[node]) for node in nodes}
    avg_magnitude = sum(magnitudes.values()) / len(magnitudes)
    
    report = {
        'sensor_count': len(nodes),
        'sensor_ids': nodes,
        'sensor_summaries': sensor_summaries,
        'flow_analysis': {
            'independent_pairs': [
                list(p) for p in analysis_result['independent_pairs']
            ],
            'independent_count': analysis_result['pair_stats']['independent_count'],
            'dependent_count': analysis_result['pair_stats']['dependent_count'],
            'total_pairs': analysis_result['pair_stats']['total_pairs']
        },
        'priority_order': analysis_result['priority_order'],
        'cross_validation': cross_validation,
        'network_metrics': {
            'average_magnitude': avg_magnitude,
            'max_magnitude': max(magnitudes.values()),
            'min_magnitude': min(magnitudes.values()),
        }
    }
    
    # Compute verification digest
    digest = hashlib.md5(
        json.dumps(report, sort_keys=True).encode()
    ).hexdigest()[:16]
    report['digest'] = digest
    
    return report
