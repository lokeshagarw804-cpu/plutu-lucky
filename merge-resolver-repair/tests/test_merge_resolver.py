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
        """Merge report output must be generated at /app/runtime/output/merge_report.json."""
        assert os.path.isfile(REPORT_PATH)

    def test_summary_file_exists(self):
        """Region summary output must be generated at /app/runtime/output/region_summary.json."""
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

    def test_all_four_strategies_recognized(self, report_data):
        """All four configured strategies must appear in output.

        The strategies list in /app/runtime/config.ini under [strategies]
        defines: recursive, patience, histogram, minimal. Check that
        /app/runtime/differ.py correctly parses all entries from the
        comma-separated merge_strategies value.
        """
        strategies = report_data["strategies_used"]
        assert "minimal" in strategies, (
            "Strategy 'minimal' not recognized. Check how "
            "/app/runtime/differ.py parses the merge_strategies config "
            "value from /app/runtime/config.ini [strategies] section — "
            "ensure all entries are properly stripped of whitespace."
        )
        assert len(strategies) == 4, (
            f"Expected 4 strategies but got {len(strategies)}: {strategies}. "
            "Verify whitespace handling in strategy list parsing."
        )

    def test_strategies_sorted(self, report_data):
        """Strategies list must be sorted alphabetically."""
        strategies = report_data["strategies_used"]
        assert strategies == sorted(strategies)


class TestConflictClassification:
    """Conflict threshold classification accuracy."""

    def test_total_conflict_count(self, report_data):
        """Exactly 6 hunks should be classified as conflicts.

        The strict threshold from [merge.strict] section (conflict_threshold=15)
        should be used. Check which config section /app/runtime/classifier.py
        reads the conflict_threshold from — it should use merge.strict, not merge.
        """
        assert report_data["total_conflicts"] == 6, (
            f"Expected 6 conflicts but got {report_data['total_conflicts']}. "
            "Check which config section /app/runtime/classifier.py reads "
            "conflict_threshold from — it should use [merge.strict] "
            "(conflict_threshold=15), not [merge] (conflict_threshold=50)."
        )

    def test_auto_resolved_count(self, report_data):
        """Exactly 4 hunks should be auto-resolved with strict threshold."""
        assert report_data["total_auto_resolved"] == 4, (
            f"Expected 4 auto-resolved but got {report_data['total_auto_resolved']}. "
            "With strict threshold=15, hunks scoring >= 15 are auto-resolved."
        )

    def test_conflict_plus_auto_equals_total(self, report_data):
        """Sum of conflicts and auto-resolved must equal total hunks (10)."""
        total = report_data["total_conflicts"] + report_data["total_auto_resolved"]
        assert total == 10, f"Expected 10 total hunks but got {total}"


class TestRegionScoring:
    """Region-level conflict score validation."""

    def test_region_count(self, summary_data):
        """System should identify exactly 4 line regions."""
        assert summary_data["total_regions"] == 4

    def test_conflicting_region_count(self, summary_data):
        """Exactly 3 regions should contain conflicts (with strict threshold)."""
        assert summary_data["conflicting_regions"] == 3, (
            f"Expected 3 conflicting regions but got "
            f"{summary_data['conflicting_regions']}."
        )

    def test_region_scores_not_accumulated(self, summary_data):
        """Region scores must reflect final hunk severity, not accumulated sum.

        Each region score should be in range 70-100 (single hunk severity).
        Accumulated scores would exceed 150. Check /app/runtime/scorer.py
        to verify it uses last-write-wins semantics for region scoring.
        """
        for region in summary_data["regions"]:
            score = region["conflict_score"]
            assert score <= 100, (
                f"Region score {score} exceeds 100, suggesting accumulation "
                f"across hunks instead of last-write-wins. Check "
                f"/app/runtime/scorer.py _compute_region_score method — "
                f"it should use the final hunk's severity, not sum all hunks."
            )

    def test_region_scores_in_expected_range(self, summary_data):
        """Region conflict scores should be between 75 and 95."""
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

    def test_same_line_ordered_by_branch_then_hunk(self, report_data):
        """Conflicts at same line must be ordered by branch_id then hunk_id.

        Since hunk_id is local to each branch, sorting by hunk_id alone
        produces non-deterministic ordering. Check /app/runtime/resolver.py
        sort key — it should be (line_start, branch_id, hunk_id).
        """
        conflicts = report_data["conflicts"]
        # Find conflicts at line 45 (multiple from different branches)
        line45 = [c for c in conflicts if c["line_start"] == 45]
        assert len(line45) >= 3, (
            f"Expected at least 3 conflicts at line 45, got {len(line45)}"
        )

        # Verify branch ordering: all 'left' before all 'right'
        branches_at_45 = [c["branch_id"] for c in line45]
        left_indices = [i for i, b in enumerate(branches_at_45) if b == "left"]
        right_indices = [i for i, b in enumerate(branches_at_45) if b == "right"]

        if left_indices and right_indices:
            assert max(left_indices) < min(right_indices), (
                f"Conflicts at line 45 not ordered by branch_id. Got order: "
                f"{branches_at_45}. Check /app/runtime/resolver.py sort key — "
                f"hunk_id is local to each branch, so branch_id must be "
                f"included for deterministic ordering."
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
