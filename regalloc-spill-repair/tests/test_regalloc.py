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
        assert os.path.isdir(OUTPUT_DIR), "Output directory was not created"

    def test_report_file_exists(self):
        """Allocation report JSON must be generated."""
        assert os.path.isfile(REPORT_FILE), "Allocation report not generated"

    def test_summary_file_exists(self):
        """Summary text file must be generated."""
        assert os.path.isfile(SUMMARY_FILE), "Summary file not generated"

    def test_report_has_required_sections(self, report):
        """Report must contain variables and statistics sections."""
        assert "variables" in report, "Report missing variables section"
        assert "statistics" in report, "Report missing statistics section"
        assert len(report["variables"]) == 20, (
            "Expected 20 variables in report"
        )


# === MEDIUM TESTS (require fixing liveness interval computation) ===


class TestInterferenceGraph:
    """Tests for correct interference graph construction."""

    def test_total_interference_edges(self, report):
        """The interference graph must have the correct number of edges.
        
        With proper liveness intervals, variables that are simultaneously
        live must all appear as interfering.
        """
        total_degree = sum(
            v["degree"] for v in report["variables"].values()
        )
        num_edges = total_degree // 2
        assert num_edges == 64, (
            f"Interference graph has {num_edges} edges, expected 64 — "
            f"live interval computation may have boundary errors"
        )

    def test_high_degree_variable(self, report):
        """The most connected variable must have correct degree."""
        max_degree = max(
            v["degree"] for v in report["variables"].values()
        )
        assert max_degree == 11, (
            f"Maximum degree is {max_degree}, expected 11 — "
            f"interval overlap detection may be incorrect"
        )

    def test_adjacent_variables_interfere(self, report):
        """Variables with adjacent live ranges must correctly interfere.
        
        When one variable's last use is at the same point another begins,
        they are simultaneously live and must conflict.
        """
        v7_degree = report["variables"]["v7"]["degree"]
        v8_degree = report["variables"]["v8"]["degree"]
        assert v7_degree == 4, (
            f"v7 degree is {v7_degree}, expected 4 — "
            f"adjacent interval overlap not detected"
        )
        assert v8_degree == 6, (
            f"v8 degree is {v8_degree}, expected 6 — "
            f"boundary condition in liveness computation"
        )

    def test_interval_representation(self, report):
        """Live intervals must use half-open representation [start, end)."""
        v0_interval = report["variables"]["v0"]["interval"]
        assert v0_interval == [0, 8], (
            f"v0 interval is {v0_interval}, expected [0, 8] — "
            f"interval endpoint computation incorrect"
        )


# === HARD TESTS (require fixing 3-4 bugs across multiple modules) ===


class TestSpillDecisions:
    """Tests for correct spill cost computation and allocation decisions."""

    def test_spill_count(self, report):
        """Correct number of variables must be spilled."""
        stats = report["statistics"]
        assert stats["spilled"] == 6, (
            f"Spilled {stats['spilled']} variables, expected 6 — "
            f"simplification threshold or spill selection is wrong"
        )

    def test_registers_used(self, report):
        """All 4 available registers must be utilized."""
        stats = report["statistics"]
        assert stats["registers_used"] == 4, (
            f"Used {stats['registers_used']} registers, expected 4 — "
            f"coloring may have unnecessary constraints"
        )

    def test_spilled_variables_identity(self, report):
        """The correct set of variables must be chosen for spilling.
        
        Spill decisions depend on cost computation and simplification order.
        """
        spilled = sorted(
            var for var, info in report["variables"].items()
            if info["spilled"]
        )
        expected_spilled = ["v12", "v13", "v17", "v2", "v6", "v9"]
        assert spilled == expected_spilled, (
            f"Spilled {spilled}, expected {expected_spilled} — "
            f"spill cost ranking or simplification condition is incorrect"
        )

    def test_deeply_nested_spill_cost(self, report):
        """Variables in deep loops must have exponentially higher spill costs."""
        v19_cost = report["variables"]["v19"]["spill_cost"]
        assert abs(v19_cost - 66.6667) < 0.01, (
            f"v19 spill cost is {v19_cost}, expected ~66.6667 — "
            f"loop nesting factor computation may be wrong"
        )

    def test_v5_register_assignment(self, report):
        """Variable v5 must be allocated with correct register assignment."""
        v5_info = report["variables"]["v5"]
        assert not v5_info["spilled"], (
            "v5 should be allocated to a register, not spilled"
        )
        assert v5_info["register"] == "R3", (
            f"v5 assigned to {v5_info['register']}, expected R3"
        )

    def test_v3_not_spilled(self, report):
        """Variable v3 (high degree, moderate cost) must NOT be spilled.
        
        With correct spill costs accounting for loop depth, v3's cost
        should be high enough to avoid spilling despite its high degree.
        """
        v3_info = report["variables"]["v3"]
        assert not v3_info["spilled"], (
            "v3 should be allocated to a register — "
            "spill cost computation may be incorrect"
        )
        assert v3_info["register"] == "R2", (
            f"v3 assigned to {v3_info['register']}, expected R2"
        )

    def test_coloring_uses_register_zero(self, report):
        """Register R0 must be assigned to at least one variable.
        
        Correct coloring without phantom constraints should freely use R0.
        """
        r0_vars = [
            var for var, info in report["variables"].items()
            if info.get("color") == 0 and not info["spilled"]
        ]
        assert len(r0_vars) >= 3, (
            f"Only {len(r0_vars)} variables use R0, expected at least 3 — "
            f"register 0 may be unnecessarily constrained"
        )

    def test_allocation_completeness(self, report):
        """Every variable must be either allocated or explicitly spilled."""
        stats = report["statistics"]
        assert stats["allocated"] + stats["spilled"] == 20, (
            f"allocated ({stats['allocated']}) + spilled ({stats['spilled']}) "
            f"!= 20 total variables"
        )
        assert stats["allocated"] == 14, (
            f"Allocated {stats['allocated']} variables, expected 14"
        )
