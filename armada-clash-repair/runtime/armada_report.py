"""Armada engagement report generator.

Produces the final tactical assessment report including fleet autonomy
analysis, deployment sequencing, and integrity verification digest.
"""
import json
import hashlib
from runtime.clash_analyzer import fleets_are_autonomous, compute_deployment_priority


def build_report(vectors, armada_ids, last_event_ticks):
    """Build complete armada clash report.

    Computes all derived metrics from the engagement vectors and
    produces a signed report with integrity digest.
    """
    # Determine autonomous pairs
    autonomous_pairs = []
    sorted_ids = sorted(armada_ids)
    for i in range(len(sorted_ids)):
        for j in range(i + 1, len(sorted_ids)):
            if fleets_are_autonomous(vectors[sorted_ids[i]], vectors[sorted_ids[j]]):
                autonomous_pairs.append([sorted_ids[i], sorted_ids[j]])

    # Compute deployment priority
    deployment_order = compute_deployment_priority(armada_ids, vectors, last_event_ticks)

    # Build report structure
    report = {
        'vectors': {aid: vectors[aid] for aid in sorted_ids},
        'autonomous_pairs': autonomous_pairs,
        'deployment_order': deployment_order,
        'fleet_count': len(armada_ids),
        'total_engagements': sum(sum(v) - 3 * len(v) for v in vectors.values()),
        'digest': _compute_digest(vectors, autonomous_pairs, deployment_order, sorted_ids)
    }
    return report


def _compute_digest(vectors, autonomous_pairs, deployment_order, sorted_ids):
    """Compute SHA256 integrity digest over critical report fields.

    Incorporates vector states, autonomy determinations, and deployment
    ordering to detect any inconsistency in the analysis pipeline.
    """
    canonical = []
    for aid in sorted_ids:
        canonical.append(f"{aid}:{vectors[aid]}")
    canonical.append(f"autonomous:{autonomous_pairs}")
    canonical.append(f"deploy:{deployment_order}")
    content = '|'.join(canonical)
    return hashlib.sha256(content.encode()).hexdigest()
