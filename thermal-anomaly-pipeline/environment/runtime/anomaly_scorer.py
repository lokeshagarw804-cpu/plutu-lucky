"""
Anomaly scoring engine.
Computes weighted severity scores for threshold breach events.
Uses zone-specific weight factors for multi-dimensional scoring.
"""
from typing import List, Dict, Any


def compute_base_score(breach: Dict[str, Any], threshold_high: float,
                       threshold_critical: float) -> float:
    """
    Compute base anomaly score from breach magnitude.
    Score scales with how far the reading exceeds the threshold.
    """
    max_temp = breach['max_temp']
    if breach['severity'] == 'critical':
        # Critical: base score starts at 80
        overshoot = max_temp - threshold_critical
        base = 80.0 + min(overshoot * 2.0, 20.0)
    elif breach['severity'] == 'high':
        # High: base score 50-79
        overshoot = max_temp - threshold_high
        range_size = threshold_critical - threshold_high
        ratio = min(overshoot / range_size, 1.0) if range_size > 0 else 0.5
        base = 50.0 + ratio * 29.0
    else:
        # Elevated: base score 20-49
        base = 20.0 + (breach['mean_temp'] - threshold_high) * 2.0
        base = min(base, 49.0)

    return round(base, 2)


def apply_weight_factors(base_score: float, weight_factors: List[float],
                         breach: Dict[str, Any]) -> float:
    """
    Apply zone-specific weight factors to the base score.
    Weight factors account for:
      - sensor reliability (factor 0)
      - zone criticality (factor 1)
      - historical frequency (factor 2, optional)

    Final score = base_score * product(weight_factors adjusted by breach context)
    """
    if not weight_factors:
        return base_score

    accumulated_weight = 0.0
    for i, factor in enumerate(weight_factors):
        # Adjust factor based on breach characteristics
        if i == 0:
            # Sensor reliability: scale by breach_count ratio
            adjusted = factor * (breach['breach_count'] / max(breach['reading_count'], 1))
        elif i == 1:
            # Zone criticality: direct application
            adjusted = factor
        else:
            # Historical frequency: diminishing contribution
            adjusted = factor * (0.5 ** (i - 1))

        accumulated_weight = adjusted

    # Final score combines base with accumulated weight modifier
    final_score = base_score * (1.0 + accumulated_weight)
    return round(final_score, 2)


def score_breaches(breaches: List[Dict[str, Any]], threshold_high: float,
                   threshold_critical: float, weight_factors: List[float]) -> List[Dict[str, Any]]:
    """
    Score all breach events for a zone.
    Returns breaches augmented with computed severity scores.
    """
    scored = []
    for breach in breaches:
        base = compute_base_score(breach, threshold_high, threshold_critical)
        final = apply_weight_factors(base, weight_factors, breach)
        scored_breach = dict(breach)
        scored_breach['base_score'] = base
        scored_breach['final_score'] = final
        scored.append(scored_breach)

    return scored
