# PLUTU-LUCKY-CANARY
"""End-to-end tests for lattice signal propagation simulator.

Validates the synthesis report output against expected reference values
for the configured 7-node lattice topology and input signal traces.
"""

import json
import math
import os

import pytest


REPORT_PATH = "/app/runtime/output/synthesis_report.json"


@pytest.fixture
def report():
    """Load the synthesis report produced by the pipeline."""
    assert os.path.exists(REPORT_PATH), f"Synthesis report not found at {REPORT_PATH}"
    with open(REPORT_PATH, 'r') as f:
        return json.load(f)


class TestPathEnumeration:
    """Tests for correct path discovery through the lattice."""

    def test_total_paths_found(self, report):
        """All valid simple paths should be enumerated."""
        assert report['total_paths_found'] == 14

    def test_paths_exceed_buggy_count(self, report):
        """Path count must be greater than what incomplete DFS would find."""
        assert report['total_paths_found'] > 10


class TestPropagationDelays:
    """Tests for propagation delay computation."""

    def test_delay_0_to_6(self, report):
        """Minimum delay from node 0 to node 6 via shortest path."""
        assert abs(report['propagation_delays']['0->6'] - 0.006) < 1e-6

    def test_delay_3_to_6(self, report):
        """Minimum delay from node 3 to node 6."""
        assert abs(report['propagation_delays']['3->6'] - 0.007) < 1e-6

    def test_delay_5_to_6(self, report):
        """Minimum delay from node 5 to node 6 (direct edge)."""
        assert abs(report['propagation_delays']['5->6'] - 0.003) < 1e-6


class TestNodeEnergies:
    """Tests for per-node energy levels."""

    def test_source_node_0_energy(self, report):
        """Node 0 energy from direct injection."""
        assert abs(report['node_energies']['0'] - 0.3632) < 0.01

    def test_source_node_3_energy(self, report):
        """Node 3 energy with signal injection."""
        assert abs(report['node_energies']['3'] - 1.0930) < 0.01

    def test_source_node_5_energy(self, report):
        """Node 5 receives direct injection and is a transit node."""
        assert abs(report['node_energies']['5'] - 1.1264) < 0.01

    def test_node_4_energy(self, report):
        """Node 4 receives attenuated signals from multiple paths."""
        assert abs(report['node_energies']['4'] - 0.3608) < 0.01

    def test_node_2_energy(self, report):
        """Node 2 is a transit node with multiple incoming paths."""
        assert abs(report['node_energies']['2'] - 0.8464) < 0.01

    def test_node_6_energy(self, report):
        """Node 6 is the final destination collecting all paths."""
        assert abs(report['node_energies']['6'] - 0.7529) < 0.01

    def test_node_1_energy(self, report):
        """Node 1 receives signals from node 0 directly and via node 2."""
        assert abs(report['node_energies']['1'] - 0.4725) < 0.01


class TestInterference:
    """Tests for interference pattern computation."""

    def test_node_2_interference_magnitude(self, report):
        """Node 2 receives multiple signals that should interfere."""
        assert abs(report['interference_magnitudes']['2'] - 2.7486) < 0.05

    def test_node_5_interference_magnitude(self, report):
        """Node 5 interference from multiple sources."""
        assert abs(report['interference_magnitudes']['5'] - 1.8) < 0.05

    def test_node_6_interference_magnitude(self, report):
        """Node 6 has complex multi-path interference."""
        assert abs(report['interference_magnitudes']['6'] - 1.1243) < 0.05

    def test_node_4_interference_magnitude(self, report):
        """Node 4 interference pattern."""
        assert abs(report['interference_magnitudes']['4'] - 0.8696) < 0.05

    def test_node_1_interference_magnitude(self, report):
        """Node 1 interference from paths through node 2."""
        assert abs(report['interference_magnitudes']['1'] - 0.6984) < 0.05

    def test_node_3_interference_magnitude(self, report):
        """Node 3 interference magnitude."""
        assert abs(report['interference_magnitudes']['3'] - 2.8) < 0.05


class TestResonance:
    """Tests for resonance detection."""

    def test_all_nodes_resonate(self, report):
        """With correct computation, all nodes should exceed energy threshold."""
        assert len(report['resonance_detected']) == 7

    def test_node_4_resonates(self, report):
        """Node 4 should resonate when all paths are correctly found."""
        assert 4 in report['resonance_detected']
