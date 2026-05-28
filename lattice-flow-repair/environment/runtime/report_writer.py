"""Report generation for lattice flow simulation results.

Produces the final analysis report including flow state summary,
independence classification, priority ordering, and verification digest.
"""
import hashlib
import json

from flow_analyzer import flows_are_independent


def generate_report(nodes, vectors, analysis_result, events):
    """Generate comprehensive flow analysis report.
    
    Args:
        nodes: Sorted list of junction node IDs.
        vectors: Dict mapping node_id to final pressure vector.
        analysis_result: Output from analyze_flow_pairs().
        events: List of parsed event dicts.
        
    Returns:
        Dict containing the full report structure.
    """
    # Build junction summaries
    junction_summaries = {}
    for node in nodes:
        vec = vectors[node]
        junction_summaries[node] = {
            'pressure_vector': vec,
            'vector_sum': sum(vec),
            'max_component': max(vec),
            'event_count': sum(1 for e in events if e['junction_id'] == node)
        }
    
    # Cross-validation: independently verify pair classifications
    cross_validation = {}
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            pair_key = f"{nodes[i]}:{nodes[j]}"
            cross_validation[pair_key] = {
                'independent': flows_are_independent(vectors[nodes[i]], vectors[nodes[j]])
            }
    
    report = {
        'junction_count': len(nodes),
        'junction_ids': nodes,
        'junction_summaries': junction_summaries,
        'flow_analysis': {
            'independent_pairs': [
                list(p) for p in analysis_result['independent_pairs']
            ],
            'independent_count': analysis_result['pair_stats']['independent_count'],
            'dependent_count': analysis_result['pair_stats']['dependent_count'],
            'total_pairs': analysis_result['pair_stats']['total_pairs']
        },
        'priority_order': analysis_result['priority_order'],
        'cross_validation': cross_validation
    }
    
    # Compute verification digest
    digest = hashlib.md5(
        json.dumps(report, sort_keys=True).encode()
    ).hexdigest()[:16]
    report['digest'] = digest
    
    return report
