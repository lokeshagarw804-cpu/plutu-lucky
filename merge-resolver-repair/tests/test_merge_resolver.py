"""Validation tests for merge resolution engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
REPORT_PATH = os.path.join(OUTPUT_DIR, "merge_report.json")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "region_summary.json")


@pytest.fixture(scope="module")
def report_data():
    """Load merge report output."""
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def summary_data():
    """Load region summary output."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file structure validation."""

    def test_report_file_exists(self):
        """Merge report output must be generated."""
        assert os.path.isfile(REPORT_PATH)

    def test_summary_file_exists(self):
        """Region summary output must be generated."""
        assert os.path.isfile(SUMMARY_PATH)

    def test_report_has_required_fields(self, report_data):
        """Merge report must contain all required top-level fields."""
        required = ["total_conflicts", "total_auto_resolved", "strategies_used",
                    "branch_count", "conflicts"]
        for field in required:
            assert field in report_data, f"Missing field: {field}"

    def test_summary_has_required_fields(self, summary_data):
        """Region summary must contain all required top-level fields."""
        required = ["total_regions", "conflicting_regions", "clean_regions", "regions"]
        for field in required:
            assert field in summary_data, f"Missing field: {field}"


class TestStrategyRecognition:
    """Merge strategy handling validation."""

    def test_all_configured_strategies_recognized(self, report_data):
        """Every strategy defined in configuration must appear in output."""
        strategies = report_data["strategies_used"]
        assert "minimal" in strategies, (
            "A configured strategy is missing from the output. "
            "Investigate how strategy names are parsed from the config file."
        )
        assert len(strategies) == 4, (
            f"Expected 4 strategies but got {len(strategies)}: {strategies}."
        )

    def test_strategies_sorted(self, report_data):
        """Strategies list must be sorted alphabetically."""
        strategies = report_data["strategies_used"]
        assert strategies == sorted(strategies)


class TestConflictClassification:
    """Conflict threshold classification accuracy."""

    def test_total_conflict_count(self, report_data):
        """Conflict count must match expected value for the given data and threshold."""
        assert report_data["total_conflicts"] == 6, (
            f"Expected 6 conflicts but got {report_data['total_conflicts']}. "
            "The classification threshold may not reflect production settings."
        )

    def test_auto_resolved_count(self, report_data):
        """Auto-resolved count must match expected value for production threshold."""
        assert report_data["total_auto_resolved"] == 4, (
            f"Expected 4 auto-resolved but got {report_data['total_auto_resolved']}."
        )

    def test_conflict_plus_auto_equals_total(self, report_data):
        """Sum of conflicts and auto-resolved must equal total hunks processed."""
        total = report_data["total_conflicts"] + report_data["total_auto_resolved"]
        assert total == 10, f"Expected 10 total hunks but got {total}"


class TestRegionScoring:
    """Region-level conflict score validation."""

    def test_region_count(self, summary_data):
        """System should identify exactly 4 line regions."""
        assert summary_data["total_regions"] == 4

    def test_conflicting_region_count(self, summary_data):
        """Number of conflicting regions must match expected classification."""
        assert summary_data["conflicting_regions"] == 3, (
            f"Expected 3 conflicting regions but got "
            f"{summary_data['conflicting_regions']}."
        )

    def test_region_scores_bounded(self, summary_data):
        """Region scores must not exceed theoretical maximum for a single assessment."""
        for region in summary_data["regions"]:
            score = region["conflict_score"]
            assert score <= 100, (
                f"Region score {score} exceeds maximum possible single-hunk "
                f"severity of 100. Verify the scoring aggregation logic."
            )

    def test_region_scores_in_expected_range(self, summary_data):
        """Region conflict scores should fall within valid severity bounds."""
        for region in summary_data["regions"]:
            score = region["conflict_score"]
            assert 75 <= score <= 100, (
                f"Region score {score} outside expected range [75, 100]."
            )


class TestConflictOrdering:
    """Deterministic conflict ordering validation."""

    def test_conflicts_ordered_by_line(self, report_data):
        """Conflicts must be ordered by line_start (ascending)."""
        conflicts = report_data["conflicts"]
        lines = [c["line_start"] for c in conflicts]
        assert lines == sorted(lines)

    def test_same_line_conflicts_grouped_by_branch(self, report_data):
        """Conflicts at the same line must group all entries from one branch
        before entries from another branch for deterministic output."""
        conflicts = report_data["conflicts"]
        line45 = [c for c in conflicts if c["line_start"] == 45]
        assert len(line45) >= 3, (
            f"Expected at least 3 conflicts at line 45, got {len(line45)}"
        )

        # All entries from one branch must appear contiguously
        branches_at_45 = [c["branch_id"] for c in line45]
        left_indices = [i for i, b in enumerate(branches_at_45) if b == "left"]
        right_indices = [i for i, b in enumerate(branches_at_45) if b == "right"]

        if left_indices and right_indices:
            assert max(left_indices) < min(right_indices), (
                f"Conflicts at line 45 are interleaved across branches: "
                f"{branches_at_45}. Entries from each branch must be "
                f"contiguous for deterministic output."
            )

    def test_conflict_entry_structure(self, report_data):
        """Each conflict entry must have all required fields."""
        required = ["line_start", "line_end", "branch_id", "hunk_id",
                    "severity", "strategy", "content_preview"]
        for conflict in report_data["conflicts"]:
            for field in required:
                assert field in conflict, (
                    f"Conflict entry missing field: {field}"
                )
