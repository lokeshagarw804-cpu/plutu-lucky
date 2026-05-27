"""Tests for the register allocation system."""

import json
import os
import pytest


OUTPUT_DIR = "/app/runtime/output"
REPORT_FILE = os.path.join(OUTPUT_DIR, "allocation_report.json")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "summary.txt")


@pytest.fixture
def report():
    """Load the allocation report."""
    with open(REPORT_FILE, "r") as f:
        return json.load(f)


@pytest.fixture
def summary():
    """Load the summary text."""
    with open(SUMMARY_FILE, "r") as f:
        return f.read()


# === EASY TESTS (structural, always pass) ===


class TestStructure:
    """Basic structural tests that verify output format."""

    def test_output_directory_exists(self):
        """Output directory must exist after execution."""
        assert os.path.isdir(OUTPUT_DIR)

    def test_report_file_exists(self):
        """Allocation report JSON must be generated."""
        assert os.path.isfile(REPORT_FILE)

    def test_summary_file_exists(self):
        """Summary text file must be generated."""
        assert os.path.isfile(SUMMARY_FILE)

    def test_report_has_required_sections(self, report):
        """Report must contain variables and statistics sections."""
        assert "variables" in report
        assert "statistics" in report
        assert len(report["variables"]) == 20


# === MEDIUM TESTS (require correct interference graph) ===


class TestInterferenceGraph:
    """Tests for correct interference graph construction."""

    def test_total_interference_edges(self, report):
        """The interference graph must have exactly 64 edges."""
        total_degree = sum(
            v["degree"] for v in report["variables"].values()
        )
        num_edges = total_degree // 2
        assert num_edges == 64, (
            f"Expected 64 edges, got {num_edges}"
        )

    def test_high_degree_variable(self, report):
        """The most connected variable must have degree 11."""
        max_degree = max(
            v["degree"] for v in report["variables"].values()
        )
        assert max_degree == 11, (
            f"Expected max degree 11, got {max_degree}"
        )

    def test_adjacent_variables_degrees(self, report):
        """Variables v7 and v8 must have correct degrees."""
        v7_degree = report["variables"]["v7"]["degree"]
        v8_degree = report["variables"]["v8"]["degree"]
        assert v7_degree == 4, (
            f"v7 degree: expected 4, got {v7_degree}"
        )
        assert v8_degree == 6, (
            f"v8 degree: expected 6, got {v8_degree}"
        )

    def test_v0_interval(self, report):
        """Variable v0 must have the correct live interval.
        
        The interval end should reflect exclusive-end semantics as used
        by the interference overlap check in /app/runtime/interference.py.
        """
        v0_interval = report["variables"]["v0"]["interval"]
        assert v0_interval == [0, 8], (
            f"v0 interval: expected [0, 8], got {v0_interval}"
        )


# === HARD TESTS (require fixing all interacting bugs) ===


class TestSpillDecisions:
    """Tests for correct allocation decisions."""

    def test_spill_count(self, report):
        """Exactly 6 variables must be spilled."""
        stats = report["statistics"]
        assert stats["spilled"] == 6, (
            f"Expected 6 spilled, got {stats['spilled']}"
        )

    def test_registers_used(self, report):
        """All 4 registers must be utilized."""
        stats = report["statistics"]
        assert stats["registers_used"] == 4, (
            f"Expected 4 registers used, got {stats['registers_used']}"
        )

    def test_spilled_variables_identity(self, report):
        """The correct set of variables must be spilled."""
        spilled = sorted(
            var for var, info in report["variables"].items()
            if info["spilled"]
        )
        expected_spilled = ["v12", "v13", "v17", "v2", "v6", "v9"]
        assert spilled == expected_spilled, (
            f"Expected spilled {expected_spilled}, got {spilled}"
        )

    def test_v19_spill_cost(self, report):
        """Variable v19 must have correct spill cost.
        
        v19 is at loop_depth=2 with spill_base_weight=10 from config.
        The depth factor should be base^depth (10^2=100), not base*depth.
        """
        v19_cost = report["variables"]["v19"]["spill_cost"]
        assert abs(v19_cost - 66.6667) < 0.01, (
            f"v19 spill cost: expected ~66.6667, got {v19_cost}"
        )

    def test_v5_register_assignment(self, report):
        """Variable v5 must be assigned to R3."""
        v5_info = report["variables"]["v5"]
        assert not v5_info["spilled"], "v5 should not be spilled"
        assert v5_info["register"] == "R3", (
            f"v5: expected R3, got {v5_info['register']}"
        )

    def test_v3_register_assignment(self, report):
        """Variable v3 must be assigned to R2."""
        v3_info = report["variables"]["v3"]
        assert not v3_info["spilled"], "v3 should not be spilled"
        assert v3_info["register"] == "R2", (
            f"v3: expected R2, got {v3_info['register']}"
        )

    def test_register_zero_usage(self, report):
        """Register R0 must be assigned to at least 3 variables.
        
        If R0 is under-utilized, check whether the coloring phase in
        /app/runtime/coloring.py adds false constraints from neighbors
        that have not been assigned a color yet.
        """
        r0_vars = [
            var for var, info in report["variables"].items()
            if info.get("color") == 0 and not info["spilled"]
        ]
        assert len(r0_vars) >= 3, (
            f"Expected >=3 variables on R0, got {len(r0_vars)}"
        )

    def test_allocation_completeness(self, report):
        """All 20 variables must be accounted for."""
        stats = report["statistics"]
        assert stats["allocated"] + stats["spilled"] == 20
        assert stats["allocated"] == 14, (
            f"Expected 14 allocated, got {stats['allocated']}"
        )
