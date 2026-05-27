"""Validation tests for seismic waveform coherence pipeline output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
GRID_PATH = os.path.join(OUTPUT_DIR, "coherence_grid.json")
PHASES_PATH = os.path.join(OUTPUT_DIR, "detected_phases.json")


@pytest.fixture(scope="module")
def grid_data():
    """Load coherence grid output."""
    with open(GRID_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def phases_data():
    """Load detected phases output."""
    with open(PHASES_PATH, "r") as f:
        return json.load(f)


class TestOutputGeneration:
    """Verify output files are generated with correct structure."""

    def test_grid_file_exists(self):
        """Coherence grid output must be generated."""
        assert os.path.isfile(GRID_PATH), (
            f"Expected output at {GRID_PATH}")

    def test_phases_file_exists(self):
        """Detected phases output must be generated."""
        assert os.path.isfile(PHASES_PATH), (
            f"Expected output at {PHASES_PATH}")

    def test_grid_has_required_fields(self, grid_data):
        """Grid output must contain all required fields."""
        assert "receiver_order" in grid_data
        assert "grid" in grid_data
        assert "dimensions" in grid_data

    def test_phases_has_required_fields(self, phases_data):
        """Phases output must contain all required fields."""
        assert "total_phases" in phases_data
        assert "phases" in phases_data
        assert "threshold" in phases_data


class TestReceiverOrdering:
    """Receiver ordering in coherence grid."""

    def test_receiver_count(self, grid_data):
        """Grid must include all 5 receivers."""
        assert grid_data["dimensions"] == 5

    def test_receiver_order_is_numeric(self, grid_data):
        """Receivers must be ordered by numeric identifier value."""
        order = grid_data["receiver_order"]
        expected = ["recv_1", "recv_2", "recv_3", "recv_4", "recv_10"]
        assert order == expected, (
            f"Expected {expected}, got {order}")

    def test_grid_dimensions_match(self, grid_data):
        """Grid must be NxN where N is receiver count."""
        g = grid_data["grid"]
        n = grid_data["dimensions"]
        assert len(g) == n
        assert all(len(row) == n for row in g)

    def test_grid_diagonal_is_unity(self, grid_data):
        """Diagonal entries must be 1.0 (self-coherence)."""
        g = grid_data["grid"]
        for i in range(grid_data["dimensions"]):
            assert g[i][i] == 1.0


class TestCoherenceValues:
    """Coherence coefficient magnitude validation."""

    def test_recv_1_2_strong_positive(self, grid_data):
        """Receivers 1 and 2 must show strong positive coherence."""
        g = grid_data["grid"]
        order = grid_data["receiver_order"]
        i = order.index("recv_1")
        j = order.index("recv_2")
        assert 0.85 < g[i][j] < 0.99, (
            f"Expected 0.85-0.99, got {g[i][j]}")

    def test_recv_1_4_strong_negative(self, grid_data):
        """Receivers 1 and 4 must show strong negative coherence."""
        g = grid_data["grid"]
        order = grid_data["receiver_order"]
        i = order.index("recv_1")
        j = order.index("recv_4")
        assert g[i][j] < -0.85, (
            f"Expected <-0.85, got {g[i][j]}")

    def test_recv_1_3_near_zero(self, grid_data):
        """Receivers 1 and 3 must show near-zero coherence."""
        g = grid_data["grid"]
        order = grid_data["receiver_order"]
        i = order.index("recv_1")
        j = order.index("recv_3")
        assert abs(g[i][j]) < 0.15, (
            f"Expected |val|<0.15, got {g[i][j]}")

    def test_recv_2_10_moderate_positive(self, grid_data):
        """Receivers 2 and 10 must show moderate-to-strong positive coherence."""
        g = grid_data["grid"]
        order = grid_data["receiver_order"]
        i = order.index("recv_2")
        j = order.index("recv_10")
        assert 0.75 < g[i][j] < 0.93, (
            f"Expected 0.75-0.93, got {g[i][j]}")

    def test_grid_symmetry(self, grid_data):
        """Coherence grid must be symmetric."""
        g = grid_data["grid"]
        n = grid_data["dimensions"]
        for i in range(n):
            for j in range(n):
                assert abs(g[i][j] - g[j][i]) < 1e-6, (
                    f"Asymmetry at [{i}][{j}]: {g[i][j]} vs {g[j][i]}")


class TestPhaseDetection:
    """Sustained coherence phase detection validation."""

    def test_total_phase_count(self, phases_data):
        """Must detect exactly 6 sustained coherence phases."""
        assert phases_data["total_phases"] == 6, (
            f"Expected 6, got {phases_data['total_phases']}")

    def test_constructive_phase_count(self, phases_data):
        """Must detect exactly 3 constructive phases."""
        constructive = [p for p in phases_data["phases"]
                        if p["polarity"] == "constructive"]
        assert len(constructive) == 3, (
            f"Expected 3 constructive, got {len(constructive)}")

    def test_destructive_phase_count(self, phases_data):
        """Must detect exactly 3 destructive phases."""
        destructive = [p for p in phases_data["phases"]
                       if p["polarity"] == "destructive"]
        assert len(destructive) == 3, (
            f"Expected 3 destructive, got {len(destructive)}")

    def test_constructive_recv_1_2(self, phases_data):
        """Must detect constructive phase between receivers 1 and 2."""
        phases = phases_data["phases"]
        found = any(
            p["receiver_a"] == "recv_1" and p["receiver_b"] == "recv_2"
            and p["polarity"] == "constructive"
            for p in phases
        )
        assert found, "Expected constructive phase for recv_1 <-> recv_2"

    def test_destructive_recv_1_4(self, phases_data):
        """Must detect destructive phase between receivers 1 and 4."""
        phases = phases_data["phases"]
        found = any(
            p["receiver_a"] == "recv_1" and p["receiver_b"] == "recv_4"
            and p["polarity"] == "destructive"
            for p in phases
        )
        assert found, "Expected destructive phase for recv_1 <-> recv_4"

    def test_phase_minimum_duration(self, phases_data):
        """All phases must meet minimum duration requirement."""
        for phase in phases_data["phases"]:
            assert phase["duration_windows"] >= 3, (
                f"Expected duration>=3, got {phase['duration_windows']}")

    def test_window_count_consistency(self, phases_data):
        """Phase window spans must be consistent with 7 total windows."""
        for phase in phases_data["phases"]:
            span = phase["end_window"] - phase["start_window"] + 1
            assert span == phase["duration_windows"]
            assert phase["end_window"] <= 6, (
                f"Expected max window index 6, got {phase['end_window']}")

    def test_full_span_phases_have_7_windows(self, phases_data):
        """Full-span phases must cover all 7 windows (indices 0 through 6)."""
        # Phases spanning the entire recording must have duration = 7
        full_span = [p for p in phases_data["phases"]
                     if p["start_window"] == 0
                     and p["receiver_a"] == "recv_1"
                     and p["receiver_b"] == "recv_2"]
        assert len(full_span) == 1, (
            f"Expected 1 full-span phase for recv_1<->recv_2, got {len(full_span)}")
        assert full_span[0]["duration_windows"] == 7, (
            f"Expected duration 7, got {full_span[0]['duration_windows']}")
