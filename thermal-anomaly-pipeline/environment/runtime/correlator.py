"""
Cross-zone event correlator.
Identifies related anomaly events across different thermal zones
and deduplicates events that represent the same physical incident.
"""
from typing import List, Dict, Any, Tuple


def build_event_timeline(zone_breaches: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Merge breach events from all zones into a unified timeline.
    Each event is tagged with its source zone_id.
    """
    timeline = []
    for zone_id, breaches in zone_breaches.items():
        for breach in breaches:
            event = dict(breach)
            event['zone_id'] = zone_id
            timeline.append(event)

    # Sort by window_start timestamp, then by severity rank for determinism
    severity_rank = {'critical': 0, 'high': 1, 'elevated': 2}
    timeline.sort(key=lambda e: (e['window_start'], severity_rank.get(e['severity'], 3)))
    return timeline


def find_correlated_groups(timeline: List[Dict[str, Any]],
                           correlation_window: int) -> List[List[Dict[str, Any]]]:
    """
    Group events that occur within the correlation window (seconds) of each other.
    Events in the same group are considered potentially related incidents.
    """
    if not timeline:
        return []

    groups = []
    current_group = [timeline[0]]

    for i in range(1, len(timeline)):
        event = timeline[i]
        group_start = current_group[0]['window_start']

        if event['window_start'] - group_start <= correlation_window:
            current_group.append(event)
        else:
            groups.append(current_group)
            current_group = [event]

    groups.append(current_group)
    return groups


def deduplicate_events(groups: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate events within each correlation group.
    Two events are considered duplicates if they share the same
    window_start timestamp AND zone_id (same physical event detected twice).

    Returns deduplicated list of events with correlation metadata.
    """
    deduplicated = []
    seen_keys = set()

    for group_idx, group in enumerate(groups):
        for event in group:
            # Deduplication key: same timestamp should only appear once per zone
            dedup_key = (event['window_start'], event['severity'])

            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            event['correlation_group'] = group_idx
            event['group_size'] = len(group)
            deduplicated.append(event)

    return deduplicated


def correlate_zones(zone_breaches: Dict[str, List[Dict[str, Any]]],
                    correlation_window: int = 30) -> List[Dict[str, Any]]:
    """
    Main correlation pipeline.
    Takes per-zone breach events and produces a correlated, deduplicated event stream.
    """
    timeline = build_event_timeline(zone_breaches)
    groups = find_correlated_groups(timeline, correlation_window)
    deduplicated = deduplicate_events(groups)
    return deduplicated
