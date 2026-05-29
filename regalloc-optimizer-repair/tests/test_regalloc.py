# PLUTU-LUCKY-CANARY
"""
Tests for the register allocator optimization pipeline.
Validates the optimization_report.json output against expected correct values.
"""

import json
import pytest


REPORT_PATH = "/app/runtime/output/optimization_report.json"
# Fallback for local testing outside Docker
LOCAL_REPORT_PATH = None


@pytest.fixture
def report():
    """Load the optimization report."""
    import os
    path = REPORT_PATH
    if not os.path.exists(path):
        # Try relative to the environment directory
        alt = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "environment", "runtime", "output", "optimization_report.json")
        if os.path.exists(alt):
            path = alt
    with open(path) as f:
        return json.load(f)


class TestProgramAlpha:
    """Tests for program_alpha register allocation results."""

    def test_total_instructions(self, report):
        assert report["programs"]["alpha"]["total_instructions"] == 13

    def test_registers_used(self, report):
        assert report["programs"]["alpha"]["registers_used"] == 7

    def test_spills_inserted(self, report):
        assert report["programs"]["alpha"]["spills_inserted"] == 0

    def test_moves_coalesced(self, report):
        assert report["programs"]["alpha"]["moves_coalesced"] == 0

    def test_schedule_stalls(self, report):
        assert report["programs"]["alpha"]["schedule_stalls"] == 4

    def test_interference_edges(self, report):
        assert report["programs"]["alpha"]["interference_edges"] == 36

    def test_coloring_rounds(self, report):
        assert report["programs"]["alpha"]["coloring_rounds"] == 1

    def test_registers_within_limit(self, report):
        assert report["programs"]["alpha"]["registers_used"] <= 8

    def test_no_excessive_spills(self, report):
        assert report["programs"]["alpha"]["spills_inserted"] <= 1


class TestProgramBeta:
    """Tests for program_beta register allocation results."""

    def test_total_instructions(self, report):
        assert report["programs"]["beta"]["total_instructions"] == 15

    def test_registers_used(self, report):
        assert report["programs"]["beta"]["registers_used"] == 6

    def test_spills_inserted(self, report):
        assert report["programs"]["beta"]["spills_inserted"] == 0

    def test_moves_coalesced(self, report):
        assert report["programs"]["beta"]["moves_coalesced"] == 2

    def test_schedule_stalls(self, report):
        assert report["programs"]["beta"]["schedule_stalls"] == 6

    def test_interference_edges(self, report):
        assert report["programs"]["beta"]["interference_edges"] == 31

    def test_coloring_rounds(self, report):
        assert report["programs"]["beta"]["coloring_rounds"] == 1

    def test_registers_within_limit(self, report):
        assert report["programs"]["beta"]["registers_used"] <= 8

    def test_no_excessive_spills(self, report):
        assert report["programs"]["beta"]["spills_inserted"] <= 1


class TestSummary:
    """Tests for the summary section of the optimization report."""

    def test_total_spills(self, report):
        assert report["summary"]["total_spills"] == 0

    def test_total_moves_coalesced(self, report):
        assert report["summary"]["total_moves_coalesced"] == 2

    def test_total_stalls(self, report):
        assert report["summary"]["total_stalls"] == 10

    def test_allocation_success(self, report):
        assert report["summary"]["allocation_success"] is True

    def test_verification_passed(self, report):
        assert report["summary"]["verification_passed"] is True

    def test_spills_sum_matches(self, report):
        alpha_spills = report["programs"]["alpha"]["spills_inserted"]
        beta_spills = report["programs"]["beta"]["spills_inserted"]
        assert report["summary"]["total_spills"] == alpha_spills + beta_spills

    def test_coalesced_sum_matches(self, report):
        alpha_coal = report["programs"]["alpha"]["moves_coalesced"]
        beta_coal = report["programs"]["beta"]["moves_coalesced"]
        assert report["summary"]["total_moves_coalesced"] == alpha_coal + beta_coal

    def test_stalls_sum_matches(self, report):
        alpha_stalls = report["programs"]["alpha"]["schedule_stalls"]
        beta_stalls = report["programs"]["beta"]["schedule_stalls"]
        assert report["summary"]["total_stalls"] == alpha_stalls + beta_stalls


class TestReportStructure:
    """Tests for report structure and completeness."""

    def test_has_programs_key(self, report):
        assert "programs" in report

    def test_has_summary_key(self, report):
        assert "summary" in report

    def test_has_alpha(self, report):
        assert "alpha" in report["programs"]

    def test_has_beta(self, report):
        assert "beta" in report["programs"]

    def test_alpha_has_all_fields(self, report):
        expected_fields = [
            "total_instructions", "registers_used", "spills_inserted",
            "moves_coalesced", "schedule_stalls", "interference_edges",
            "coloring_rounds"
        ]
        for field in expected_fields:
            assert field in report["programs"]["alpha"], f"Missing field: {field}"

    def test_beta_has_all_fields(self, report):
        expected_fields = [
            "total_instructions", "registers_used", "spills_inserted",
            "moves_coalesced", "schedule_stalls", "interference_edges",
            "coloring_rounds"
        ]
        for field in expected_fields:
            assert field in report["programs"]["beta"], f"Missing field: {field}"
