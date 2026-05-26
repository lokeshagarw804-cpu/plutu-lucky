"""
Tests for the three-way merge engine.

Validates diff computation, conflict detection, resolution
correctness, and assembled output integrity.
"""
import json
import os
import pytest


MERGED_PATH = "/app/runtime/output/merged_document.json"
CONFLICTS_PATH = "/app/runtime/output/conflict_report.json"
SUMMARY_PATH = "/app/runtime/output/merge_summary.json"


def load_merged():
    with open(MERGED_PATH, "r") as f:
        return json.load(f)


def load_conflicts():
    with open(CONFLICTS_PATH, "r") as f:
        return json.load(f)


def load_summary():
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


# --- EASY TESTS (always pass) ---

class TestOutputStructure:
    """Basic output file presence and format."""

    def test_merged_document_exists(self):
        """Merged document output must exist."""
        assert os.path.isfile(MERGED_PATH)

    def test_conflict_report_exists(self):
        """Conflict report output must exist."""
        assert os.path.isfile(CONFLICTS_PATH)

    def test_summary_exists(self):
        """Merge summary output must exist."""
        assert os.path.isfile(SUMMARY_PATH)

    def test_merged_has_sections(self):
        """Merged document must contain section entries."""
        m = load_merged()
        assert "sections" in m
        assert len(m["sections"]) == 5


# --- MEDIUM TESTS (require 1-2 fixes) ---

class TestConflictDetection:
    """Verify correct identification of merge conflicts."""

    def test_conflict_count(self):
        """Only 2 true conflicts should be detected across all sections.

        A conflict requires overlapping change regions from both branches
        where neither change is a pure addition. Most non-overlapping
        changes should be auto-resolved without conflict.
        """
        c = load_conflicts()
        assert c["total_conflicts"] == 2, (
            f"Expected 2 conflicts, got {c['total_conflicts']}. "
            "Verify the conflict detection logic correctly identifies "
            "overlapping regions versus non-overlapping changes."
        )

    def test_auto_resolved_count(self):
        """Non-conflicting changes should be auto-resolved (18 total)."""
        s = load_summary()
        assert s["total_auto_resolved"] == 18, (
            f"Expected 18 auto-resolved changes, got "
            f"{s['total_auto_resolved']}"
        )

    def test_sections_without_conflicts(self):
        """Sections S03, S04, S05 should have zero conflicts."""
        c = load_conflicts()
        conflict_sections = set(
            d["section_id"] for d in c["conflict_details"]
        )
        for sid in ["S03", "S04", "S05"]:
            assert sid not in conflict_sections, (
                f"Section {sid} should have no conflicts but is listed"
            )


# --- MEDIUM-HARD TESTS (require 2-3 fixes) ---

class TestMergedContent:
    """Verify merged output correctness."""

    def test_section_line_counts(self):
        """Each merged section must have the correct line count.

        Sections should grow due to additions from both branches.
        Expected: S01=6, S02=6, S03=7, S04=7, S05=7.
        """
        m = load_merged()
        expected = {"S01": 6, "S02": 6, "S03": 7, "S04": 7, "S05": 7}
        for section in m["sections"]:
            sid = section["id"]
            actual = len(section["lines"])
            assert actual == expected[sid], (
                f"Section {sid}: expected {expected[sid]} lines, "
                f"got {actual}"
            )

    def test_additions_from_both_branches(self):
        """Both branch additions must appear in conflict-free sections.

        Section S03 should include both '/api/v1/analytics' (from A)
        and '/api/v1/webhooks' (from B) since they are non-conflicting
        additions appended to the section.
        """
        m = load_merged()
        s03 = next(s for s in m["sections"] if s["id"] == "S03")
        assert "/api/v1/analytics" in s03["lines"], (
            "Branch A addition '/api/v1/analytics' missing from S03"
        )
        assert "/api/v1/webhooks" in s03["lines"], (
            "Branch B addition '/api/v1/webhooks' missing from S03"
        )

    def test_total_merged_lines(self):
        """Total line count across all sections should be 33."""
        m = load_merged()
        total = sum(len(s["lines"]) for s in m["sections"])
        assert total == 33, (
            f"Expected 33 total merged lines, got {total}"
        )


# --- HARD TESTS (require all fixes together) ---

class TestResolutionAccuracy:
    """Verify conflict resolution produces correct winners."""

    def test_branch_a_wins_conflicts(self):
        """With branch_a_first precedence at depth 1, branch A lines win.

        In section S01, branch A changes lines 0-1 (flask, requests) and
        branch B also changes line 1 (requests). The conflict should
        resolve to branch A's version of the conflicting lines.
        """
        m = load_merged()
        s01 = next(s for s in m["sections"] if s["id"] == "S01")
        # Branch A upgraded flask to 2.1.0 and requests to 2.27.1
        assert "flask==2.1.0" in s01["lines"], (
            "Expected branch A's flask==2.1.0 to win the conflict"
        )
        assert "requests==2.27.1" in s01["lines"], (
            "Expected branch A's requests==2.27.1 to win the conflict"
        )

    def test_no_data_loss_in_assembly(self):
        """Assembled sections must not lose lines due to boundary errors.

        Each change region uses inclusive boundaries. If the assembly
        step uses exclusive slicing on inclusive ranges, the last line
        of each applied change will be silently dropped.
        """
        m = load_merged()
        # S04 should have metrics_collector (last addition from A)
        s04 = next(s for s in m["sections"] if s["id"] == "S04")
        assert "metrics_collector" in s04["lines"], (
            "Addition 'metrics_collector' missing - check slice boundaries "
            "in the assembler for inclusive vs exclusive ranges"
        )
        # S05 should have health_check (last addition from A)
        s05 = next(s for s in m["sections"] if s["id"] == "S05")
        assert "health_check:*/5 * * * *" in s05["lines"], (
            "Addition 'health_check' missing from S05 - the assembler "
            "may be dropping the last line of each applied region"
        )
