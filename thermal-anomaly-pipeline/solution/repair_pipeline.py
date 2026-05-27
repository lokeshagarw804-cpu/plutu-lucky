#!/usr/bin/env python3
"""
Repair script for the Thermal Anomaly Detection Pipeline.
Fixes three bugs:
1. anomaly_scorer.py: Weight accumulator uses assignment instead of +=
2. correlator.py: Dedup key missing zone_id, causing cross-zone event loss
3. alert_builder.py: Sort key missing timestamp tiebreaker for deterministic ordering
"""
import os
import re

RUNTIME_DIR = os.path.join(os.path.dirname(__file__), '..', 'environment', 'runtime')


def fix_anomaly_scorer():
    """Fix bug: accumulated_weight = adjusted -> accumulated_weight += adjusted"""
    filepath = os.path.join(RUNTIME_DIR, 'anomaly_scorer.py')
    with open(filepath, 'r') as f:
        content = f.read()

    # Fix the assignment bug - should be accumulation
    content = content.replace(
        'accumulated_weight = adjusted',
        'accumulated_weight += adjusted'
    )

    with open(filepath, 'w') as f:
        f.write(content)
    print(f"[FIXED] {filepath}: Weight factor accumulation corrected")


def fix_correlator():
    """Fix bug: dedup key must include zone_id to prevent cross-zone event loss"""
    filepath = os.path.join(RUNTIME_DIR, 'correlator.py')
    with open(filepath, 'r') as f:
        content = f.read()

    # Fix the deduplication key to include zone_id
    content = content.replace(
        "dedup_key = (event['window_start'], event['severity'])",
        "dedup_key = (event['window_start'], event['severity'], event['zone_id'])"
    )

    with open(filepath, 'w') as f:
        f.write(content)
    print(f"[FIXED] {filepath}: Deduplication key now includes zone_id")


def fix_alert_builder():
    """Fix bug: alert ordering must include score and timestamp for deterministic ordering"""
    filepath = os.path.join(RUNTIME_DIR, 'alert_builder.py')
    with open(filepath, 'r') as f:
        content = f.read()

    # Fix the sort key to include score and timestamp for deterministic ordering
    old_code = "    return (rank,)"
    new_code = "    return (rank, -event.get('final_score', 0), event['window_start'])"

    content = content.replace(old_code, new_code)

    with open(filepath, 'w') as f:
        f.write(content)
    print(f"[FIXED] {filepath}: Alert ordering now includes score and timestamp")


if __name__ == '__main__':
    fix_anomaly_scorer()
    fix_correlator()
    fix_alert_builder()
    print("\nAll fixes applied. Run tests to verify.")
