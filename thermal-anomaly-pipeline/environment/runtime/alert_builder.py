"""
Alert batch builder.
Constructs final alert records from correlated events,
applying priority ordering and batch size constraints.
"""
from typing import List, Dict, Any, Tuple
import hashlib
import json


def compute_alert_priority(event: Dict[str, Any]) -> Tuple:
    """
    Compute sort key for alert priority ordering.
    Alerts should be ordered by:
      1. Severity (critical > high > elevated) - descending
      2. Final score - descending
      3. Timestamp - ascending (earliest first for same severity/score)

    This ensures deterministic, reproducible alert ordering.
    """
    severity_rank = {'critical': 0, 'high': 1, 'elevated': 2}
    rank = severity_rank.get(event['severity'], 3)
    return (rank,)


def build_alert_record(event: Dict[str, Any], alert_index: int) -> Dict[str, Any]:
    """
    Construct a structured alert record from a correlated event.
    """
    # Generate deterministic alert ID from event properties
    id_source = f"{event['zone_id']}:{event['window_start']}:{event['severity']}"
    alert_id = hashlib.md5(id_source.encode()).hexdigest()[:12]

    return {
        'alert_id': alert_id,
        'index': alert_index,
        'zone_id': event['zone_id'],
        'severity': event['severity'],
        'timestamp': event['window_start'],
        'max_temperature': event['max_temp'],
        'mean_temperature': event['mean_temp'],
        'base_score': event.get('base_score', 0.0),
        'final_score': event.get('final_score', 0.0),
        'correlation_group': event.get('correlation_group', -1),
        'group_size': event.get('group_size', 1),
        'breach_count': event['breach_count'],
    }


def build_alert_batch(events: List[Dict[str, Any]], max_batch_size: int = 50) -> Dict[str, Any]:
    """
    Build a prioritized batch of alerts from correlated events.
    Returns batch metadata and ordered alert list.
    """
    # Sort events by priority
    sorted_events = sorted(events, key=compute_alert_priority)

    # Trim to batch size
    batch_events = sorted_events[:max_batch_size]

    # Build alert records
    alerts = []
    for i, event in enumerate(batch_events):
        alert = build_alert_record(event, i)
        alerts.append(alert)

    # Compute batch summary
    severity_counts = {}
    total_score = 0.0
    for alert in alerts:
        sev = alert['severity']
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        total_score += alert['final_score']

    batch = {
        'batch_size': len(alerts),
        'severity_counts': severity_counts,
        'total_score': round(total_score, 2),
        'alerts': alerts,
    }

    return batch
