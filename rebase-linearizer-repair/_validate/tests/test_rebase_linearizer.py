"""Validation tests for rebase linearization engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/projects/sandbox/plutu-lucky/rebase-linearizer-repair/_validate/app/runtime/output"
PLAN_PATH = os.path.join(OUTPUT_DIR, "rebase_plan.json")
REPORT_PATH = os.path.join(OUTPUT_DIR, "conflict_report.json")


@pytest.fixture(scope="module")
def plan_data():
    """Load rebase plan output."""
    with open(PLAN_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def report_data():
    """Load conflict report output."""
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file structure validation."""

    def test_plan_file_exists(self):
        """Rebase plan output must be generated."""
        assert os.path.isfile(PLAN_PATH)

    def test_report_file_exists(self):
        """Conflict report output must be generated."""
        assert os.path.isfile(REPORT_PATH)

    def test_plan_has_required_fields(self, plan_data):
        """Rebase plan must contain all required top-level fields."""
        required = ["total_commits", "total_groups", "commits", "groups"]
        for field in required:
            assert field in plan_data, f"Missing field: {field}"

    def test_report_has_required_fields(self, report_data):
        """Conflict report must contain all required top-level fields."""
        required = ["total_conflicts", "total_commits_analyzed", "conflicts"]
        for field in required:
            assert field in report_data, f"Missing field: {field}"


class TestCommitFiltering:
    """Commit filtering and skip pattern validation."""

    def test_total_commits_analyzed(self, report_data):
        """All source commits should be counted regardless of filtering."""
        assert report_data["total_commits_analyzed"] == 49

    def test_plan_commit_count(self, plan_data):
        """Plan should contain only non-skipped commits."""
        assert plan_data["total_commits"] == 29, (
            f"Expected 29 commits in plan but got {plan_data['total_commits']}. "
            "Commit filtering is not working correctly."
        )

    def test_no_skipped_patch_types_in_plan(self, plan_data):
        """Commits matching skip patterns must not appear in the rebase plan."""
        disallowed = {"test_", "mock_", "fixture_", "setup_"}
        for commit in plan_data["commits"]:
            assert commit["patch_type"] not in disallowed, (
                "A commit with a skippable patch type appears in the plan. "
                "Commit filtering is not working correctly."
            )

    def test_setup_commits_excluded(self, plan_data):
        """Setup-type commits must be filtered from the rebase plan."""
        setup_count = sum(
            1 for c in plan_data["commits"] if c["patch_type"] == "setup_"
        )
        assert setup_count == 0, (
            f"Found {setup_count} setup-type commits in plan. "
            "Commit filtering is not working correctly."
        )


class TestConflictDetection:
    """Conflict detection accuracy validation."""

    def test_conflicts_detected(self, report_data):
        """System must detect at least one conflict for the given data."""
        assert report_data["total_conflicts"] > 0, (
            "No conflicts detected. "
            "Conflict detection sensitivity does not match expected behavior."
        )

    def test_conflict_count(self, report_data):
        """Conflict count must match expected value for production threshold."""
        assert report_data["total_conflicts"] == 8, (
            f"Expected 8 conflicts but got {report_data['total_conflicts']}. "
            "Conflict detection sensitivity does not match expected behavior."
        )

    def test_conflict_entry_structure(self, report_data):
        """Each conflict entry must have all required fields."""
        required = ["commit_a", "commit_b", "branch_a", "branch_b",
                    "shared_files", "overlap_count"]
        for conflict in report_data["conflicts"]:
            for field in required:
                assert field in conflict, (
                    f"Conflict entry missing field: {field}"
                )

    def test_conflicts_cross_branch(self, report_data):
        """All conflicts must be between commits from different branches."""
        for conflict in report_data["conflicts"]:
            assert conflict["branch_a"] != conflict["branch_b"], (
                "Found a conflict between commits on the same branch."
            )


class TestGroupScoring:
    """Dependency group scoring validation."""

    def test_group_count(self, plan_data):
        """System should identify the expected number of dependency groups."""
        assert plan_data["total_groups"] == 6, (
            f"Expected 6 groups but got {plan_data['total_groups']}."
        )

    def test_group_priorities_bounded(self, plan_data):
        """Group priorities must not exceed theoretical single-patch maximum."""
        for group in plan_data["groups"]:
            priority = group["priority"]
            assert priority <= 100, (
                f"Group priority {priority} exceeds maximum possible "
                f"single-patch weight of 100. "
                "Group priority values are outside expected bounds."
            )

    def test_group_priorities_in_expected_range(self, plan_data):
        """Group priorities should fall within valid weight bounds."""
        for group in plan_data["groups"]:
            priority = group["priority"]
            assert 40 <= priority <= 100, (
                f"Group priority {priority} outside expected range [40, 100]. "
                "Group priority values are outside expected bounds."
            )

    def test_group_has_required_fields(self, plan_data):
        """Each group record must have all required fields."""
        required = ["commits", "branches", "size", "priority",
                    "earliest_timestamp", "latest_timestamp"]
        for group in plan_data["groups"]:
            for field in required:
                assert field in group, f"Group missing field: {field}"
