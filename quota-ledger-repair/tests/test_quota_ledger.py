"""
Graduated test suite for the resource quota allocation ledger system.
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
    """Basic structural validation."""

    def test_report_file_exists(self):
        """Verify the allocation report file was created."""
        assert os.path.exists(REPORT_PATH)

    def test_report_has_summary(self, report):
        """Verify report contains a summary section."""
        assert "summary" in report
        summary = report["summary"]
        assert "total_requests" in summary
        assert "approved_count" in summary
        assert "rejected_count" in summary
        assert "integrity_pass" in summary
        assert "integrity_fail" in summary
        assert "team_count" in summary

    def test_report_has_requests_list(self, report):
        """Verify report contains the requests list."""
        assert "requests" in report
        assert isinstance(report["requests"], list)
        assert len(report["requests"]) > 0

    def test_all_request_ids_present(self, report):
        """Verify all expected request IDs are present."""
        request_ids = {r["request_id"] for r in report["requests"]}
        expected_ids = {f"REQ-{i:03d}" for i in range(1, 39)}
        assert request_ids == expected_ids


class TestRequestCounts:
    """Validate correct request counts."""

    def test_total_request_count(self, report):
        """Total requests must be exactly 38."""
        assert report["summary"]["total_requests"] == 38

    def test_team_count(self, report):
        """Must have exactly 3 teams."""
        assert report["summary"]["team_count"] == 3

    def test_report_has_batch_order(self, report):
        """Report must include batch_order field."""
        assert "batch_order" in report
        assert isinstance(report["batch_order"], list)
        assert len(report["batch_order"]) == 3


class TestIntegrity:
    """Verify HMAC integrity checking."""

    def test_all_integrity_valid(self, report):
        """All 38 requests must pass integrity verification."""
        assert report["summary"]["integrity_fail"] == 0, (
            f"Got {report['summary']['integrity_fail']} integrity failures"
        )
        assert report["summary"]["integrity_pass"] == 38


class TestQuotaEnforcement:
    """Verify quota enforcement."""

    def test_over_quota_count(self, report):
        """Exactly 8 requests must be rejected for exceeding quota."""
        rejected = [
            r for r in report["requests"]
            if r.get("quota_status") == "rejected"
            and r.get("rejection_reason") == "over_quota"
        ]
        assert len(rejected) == 8, (
            f"Expected 8 over-quota rejections, got {len(rejected)}"
        )

    def test_approved_count(self, report):
        """Exactly 30 requests must be approved."""
        assert report["summary"]["approved_count"] == 30


class TestPriorityScoring:
    """Verify priority score computation."""

    def test_root_team_priority_score(self, report):
        """Root team requests must have priority score of 100.0."""
        root_requests = [
            r for r in report["requests"]
            if r.get("priority_group") == "platform-core"
        ]
        assert len(root_requests) > 0
        for r in root_requests:
            assert r["priority_score"] == 100.0, (
                f"{r['request_id']} has score {r['priority_score']}"
            )


class TestBatchOrdering:
    """Verify file processing order."""

    def test_batch_processing_order(self, report):
        """Batches must be in natural numeric order."""
        expected_order = ["team_1.json", "team_2.json", "team_10.json"]
        assert report["batch_order"] == expected_order
