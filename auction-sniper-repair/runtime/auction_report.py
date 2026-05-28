"""
Auction strategy report generator.

Produces the final JSON report summarizing the auction sniper simulation
results, including:
  - Bot activity vectors and weights
  - Independent strategy pair classification
  - Optimal execution ordering
  - Integrity digest for validation

This module imports and uses the StrategyChecker and BidPlanner from
strategy_evaluator.py. The report reflects the output of those classifiers
directly — if the classification logic changes, the report output changes
accordingly.
"""

import json
import hashlib
import os
from typing import Dict, List, Any, Tuple

from strategy_evaluator import StrategyChecker, BidPlanner


# ═══════════════════════════════════════════════════════════════════════
# DIGEST COMPUTATION
# ═══════════════════════════════════════════════════════════════════════

def _compute_integrity_digest(
    bot_ids: List[str],
    vectors: Dict[str, List[int]],
    independent_pairs: List[Tuple[str, str]],
    execution_order: List[str]
) -> str:
    """Compute SHA-256 integrity digest over all classification outputs.
    
    The digest incorporates:
      1. All final bid vectors (ordered by bot_id)
      2. The set of independent bot pairs
      3. The computed execution order
    
    This ensures that any discrepancy in vector computation, independence
    classification, or ordering logic will produce a different digest.
    """
    h = hashlib.sha256()
    
    # Factor 1: Bid vectors
    for bot_id in bot_ids:
        v = vectors[bot_id]
        h.update(f"{bot_id};{';'.join(map(str, v))}".encode())
    
    # Factor 2: Independent pairs
    pair_strings = [f"{a}~{b}" for a, b in independent_pairs]
    h.update(f"INDEPENDENT={';'.join(pair_strings)}".encode())
    
    # Factor 3: Execution order
    h.update(f"EXEC_ORDER={';'.join(execution_order)}".encode())
    
    return h.hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════════════
# REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════

def generate_strategy_report(
    bot_ids: List[str],
    vectors: Dict[str, List[int]],
    events: List[Dict[str, Any]],
    output_path: str
) -> Dict[str, Any]:
    """Generate the complete auction strategy report.
    
    Runs the StrategyChecker and BidPlanner on the provided data,
    then writes the report JSON to the specified output path.
    
    Args:
        bot_ids: Sorted list of bot identifiers.
        vectors: Mapping from bot_id to final activity vector.
        events: Full list of processed events.
        output_path: Path to write the JSON report.
        
    Returns:
        The complete report dictionary.
    """
    # Run classification
    checker = StrategyChecker(bot_ids, vectors)
    planner = BidPlanner(bot_ids, vectors, events)
    
    # Get results
    independent_pairs = checker.find_all_independent_pairs()
    execution_order = planner.compute_execution_order()
    activity_weights = planner.compute_activity_weights()
    
    # Compute digest
    digest = _compute_integrity_digest(
        bot_ids, vectors, independent_pairs, execution_order
    )
    
    # Build report structure
    report = {
        'session_summary': {
            'total_bots': len(bot_ids),
            'total_events': len(events),
            'bot_ids': bot_ids,
        },
        'activity_vectors': {
            bot_id: {
                'vector': vectors[bot_id],
                'own_component': vectors[bot_id][bot_ids.index(bot_id)],
                'total_weight': activity_weights[bot_id],
            }
            for bot_id in bot_ids
        },
        'independence_analysis': {
            'independent_pair_count': len(independent_pairs),
            'total_possible_pairs': len(bot_ids) * (len(bot_ids) - 1) // 2,
            'independent_pairs': [
                {'bot_a': a, 'bot_b': b} for a, b in independent_pairs
            ],
            'comparison_stats': checker.get_comparison_stats(),
        },
        'execution_plan': {
            'order': execution_order,
            'activity_weights': activity_weights,
        },
        'integrity': {
            'digest': digest,
            'digest_algorithm': 'sha256_truncated_16',
            'factors': ['vectors', 'independence_pairs', 'execution_order'],
        },
    }
    
    # Write report
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report
