"""
Graduated test suite for the resource quota allocation ledger system.

Tests verify structural correctness, request counts, integrity validation,
quota enforcement with strict limits, priority score accuracy, and batch
processing order.
"""

import json
import os
import pytest


REPORT_PATH = "/app/runtime/output/allocation_report.json"


@pytest.fixture(scope="module")
def report():
    """Load the allocation report."""
    assert os.path.exists(REPORT_PATH), f"Report not found at {REPORT_PATH}"
    with open(REPORT_PATH, "r") as fh:
        return json.load(fh)


class TestBasicStructure:
    """Basic structural validation — these should always pass."""

    def test_report_file_exists(self):
        """Verify the allocation report file was created."""
        assert os.path.exists(REPORT_PATH), "allocation_report.json must exist"

    def test_report_has_summary(self, report):
        """Verify report contains a summary section."""
        assert "summary" in report, "Report must have 'summary' key"
        summary = report["summary"]
        assert "total_requests" in summary
        assert "approved_count" in summary
        assert "rejected_count" in summary
        assert "integrity_pass" in summary
        assert "integrity_fail" in summary
        assert "team_count" in summary

    def test_report_has_requests_list(self, report):
        """Verify report contains the requests list."""
        assert "requests" in report, "Report must have 'requests' key"
        assert isinstance(report["requests"], list)
        assert len(report["requests"]) > 0

    def test_all_request_ids_present(self, report):
        """Verify all expected request IDs are present."""
        request_ids = {r["request_id"] for r in report["requests"]}
        expected_ids = {f"REQ-{i:03d}" for i in range(1, 39)}
        assert request_ids == expected_ids, (
            f"Missing IDs: {expected_ids - request_ids}, "
            f"Extra IDs: {request_ids - expected_ids}"
        )


class TestRequestCounts:
    """Validate correct request counts across teams."""

    def test_total_request_count(self, report):
        """Total requests must be exactly 38."""
        assert report["summary"]["total_requests"] == 38

    def test_team_count(self, report):
        """Must have exactly 3 teams."""
        assert report["summary"]["team_count"] == 3

    def test_report_has_batch_order(self, report):
        """Report must include batch_order field."""
        assert "batch_order" in report, "Report must have 'batch_order' key"
        assert isinstance(report["batch_order"], list)
        assert len(report["batch_order"]) == 3


class TestIntegrity:
    """Verify HMAC integrity checking works correctly."""

    def test_all_integrity_valid(self, report):
        """All 38 requests must pass integrity verification.

        The signing key in config.ini is base64-encoded. When properly
        decoded before use in HMAC computation, all signatures validate.
        """
        integrity_pass = report["summary"]["integrity_pass"]
        integrity_fail = report["summary"]["integrity_fail"]
        assert integrity_fail == 0, (
            f"Expected 0 integrity failures, got {integrity_fail}. "
            "Check that the signing key is properly base64-decoded."
        )
        assert integrity_pass == 38, (
            f"Expected 38 integrity passes, got {integrity_pass}"
        )


class TestQuotaEnforcement:
    """Verify quota enforcement uses strict limits."""

    def test_over_quota_count(self, report):
        """Exactly 8 requests must be rejected for exceeding quota.

        The [limits.strict] section defines max_allocation_units = 2000.
        Requests with requested_units > 2000 must be rejected.
        """
        rejected = [
            r for r in report["requests"]
            if r.get("quota_status") == "rejected"
            and r.get("rejection_reason") == "over_quota"
        ]
        assert len(rejected) == 8, (
            f"Expected 8 over-quota rejections (using strict limit of 2000), "
            f"got {len(rejected)}. Check config section [limits.strict]."
        )

    def test_approved_count(self, report):
        """Exactly 30 requests must be approved."""
        assert report["summary"]["approved_count"] == 30, (
            f"Expected 30 approved, got {report['summary']['approved_count']}. "
            "With strict limit of 2000 units, 8 of 38 should be rejected."
        )


class TestPriorityScoring:
    """Verify priority score decay computation."""

    def test_root_team_priority_score(self, report):
        """Root team (platform-core, distance 0) must score exactly 100.0.

        Score formula: base_priority * (decay_factor ** distance)
        For root team: 100 * (0.80 ** 0) = 100.0
        """
        root_requests = [
            r for r in report["requests"]
            if r.get("priority_group") == "platform-core"
        ]
        assert len(root_requests) > 0, "Must have platform-core requests"
        for r in root_requests:
            assert r["priority_score"] == 100.0, (
                f"Request {r['request_id']} has priority_score "
                f"{r['priority_score']}, expected 100.0. "
                "Root team (distance=0) should get base_priority * decay^0 = 100.0"
            )


class TestBatchOrdering:
    """Verify files are processed in numeric order."""

    def test_batch_processing_order(self, report):
        """Batch order must be numeric: team_1, team_2, team_10.

        Files must be sorted by the numeric suffix, not lexicographically.
        Lexicographic sort would produce: team_1, team_10, team_2 (wrong).
        """
        batch_order = report["batch_order"]
        expected_order = ["team_1.json", "team_2.json", "team_10.json"]
        assert batch_order == expected_order, (
            f"Expected numeric order {expected_order}, "
            f"got {batch_order}. Files must be sorted numerically."
        )
