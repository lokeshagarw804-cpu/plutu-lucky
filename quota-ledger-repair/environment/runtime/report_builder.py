"""
Report builder module — constructs the final allocation report from
processed requests and writes it to the configured output directory.
"""

import os
import json


def build_report(processed_requests, batch_order, config):
    """
    Build the allocation report from processed requests.

    Args:
        processed_requests: list of fully processed request dicts
        batch_order: list of team filenames in processing order
        config: application configuration

    Returns:
        The complete report dictionary
    """
    sort_field = config.get("report", "sort_field")
    direction = config.get("report", "direction")

    # Sort requests by configured field
    reverse = direction == "descending"
    sorted_requests = sorted(
        processed_requests,
        key=lambda r: r.get(sort_field, ""),
        reverse=reverse,
    )

    # Compute summary statistics
    total = len(sorted_requests)
    approved = sum(1 for r in sorted_requests if r.get("quota_status") == "approved")
    rejected = sum(1 for r in sorted_requests if r.get("quota_status") == "rejected")
    integrity_pass = sum(1 for r in sorted_requests if r.get("integrity_valid") is True)
    integrity_fail = sum(1 for r in sorted_requests if r.get("integrity_valid") is False)

    # Compute team breakdown
    teams = {}
    for r in sorted_requests:
        team = r.get("team", "unknown")
        if team not in teams:
            teams[team] = {"total": 0, "approved": 0, "rejected": 0}
        teams[team]["total"] += 1
        if r.get("quota_status") == "approved":
            teams[team]["approved"] += 1
        else:
            teams[team]["rejected"] += 1

    report = {
        "summary": {
            "total_requests": total,
            "approved_count": approved,
            "rejected_count": rejected,
            "integrity_pass": integrity_pass,
            "integrity_fail": integrity_fail,
            "team_count": len(teams),
            "teams": teams,
        },
        "batch_order": batch_order,
        "requests": sorted_requests,
    }

    return report


def write_report(report, config):
    """Write the allocation report to the configured output directory."""
    output_dir = config.get("ledger", "output_dir")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "allocation_report.json")
    with open(output_path, "w") as fh:
        json.dump(report, fh, indent=2)

    return output_path
