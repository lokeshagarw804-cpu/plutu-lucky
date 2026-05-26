"""
Main entry point for the resource quota allocation system.

Orchestrates the full allocation workflow:
1. Load team ledger files
2. Verify request integrity (HMAC signatures)
3. Validate requests against quota limits
4. Assign priority scores
5. Build and write allocation report
"""

from runtime.ledger_loader import load_config, load_team_ledgers
from runtime.integrity_checker import check_all_integrity
from runtime.quota_validator import validate_quotas
from runtime.priority_scorer import assign_priority_scores
from runtime.report_builder import build_report, write_report


def main():
    """Run the complete allocation workflow."""
    # Step 1: Load configuration and team ledgers
    config = load_config()
    team_ledgers = load_team_ledgers(config)

    # Track batch processing order
    batch_order = [filename for filename, _ in team_ledgers]

    # Flatten all requests into a single list
    all_requests = []
    for filename, requests in team_ledgers:
        all_requests.extend(requests)

    # Step 2: Verify integrity of all requests
    checked_requests = check_all_integrity(all_requests, config)

    # Step 3: Validate against quota limits
    validated_requests = validate_quotas(checked_requests, config)

    # Step 4: Assign priority scores
    scored_requests = assign_priority_scores(validated_requests, config)

    # Step 5: Build and write report
    report = build_report(scored_requests, batch_order, config)
    output_path = write_report(report, config)

    print(f"Allocation report written to: {output_path}")
    print(f"Total requests processed: {report['summary']['total_requests']}")
    print(f"Approved: {report['summary']['approved_count']}")
    print(f"Rejected: {report['summary']['rejected_count']}")
    print(f"Integrity pass: {report['summary']['integrity_pass']}")
    print(f"Integrity fail: {report['summary']['integrity_fail']}")


if __name__ == "__main__":
    main()
