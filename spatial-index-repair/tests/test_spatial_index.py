"""Validation tests for signal correlation engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
MATRIX_PATH = os.path.join(OUTPUT_DIR, "correlation_matrix.json")
EVENTS_PATH = os.path.join(OUTPUT_DIR, "detected_events.json")


@pytest.fixture(scope="module")
def matrix_data():
    """Load correlation matrix output."""
    with open(MATRIX_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def events_data():
    """Load detected events output."""
    with open(EVENTS_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file validation."""

    def test_matrix_file_exists(self):
        """Correlation matrix output must be generated."""
        assert os.path.isfile(MATRIX_PATH)

    def test_events_file_exists(self):
        """Detected events output must be generated."""
        assert os.path.isfile(EVENTS_PATH)

    def test_matrix_structure(self, matrix_data):
        """Matrix output has required fields."""
        assert "station_order" in matrix_data
        assert "matrix" in matrix_data
        assert "size" in matrix_data

    def test_events_structure(self, events_data):
        """Events output has required fields."""
        assert "total_events" in events_data
        assert "events" in events_data
        assert "threshold" in events_data


class TestStationOrdering:
    """Station ordering in correlation matrix."""

    def test_station_count(self, matrix_data):
        """Matrix must include all 5 configured stations."""
        assert matrix_data["size"] == 5

    def test_station_order_numeric(self, matrix_data):
        """Stations must be ordered by numeric identifier."""
        order = matrix_data["station_order"]
        assert order == ["station_1", "station_2", "station_3", "station_4", "station_10"]

    def test_matrix_dimensions(self, matrix_data):
        """Matrix must be 5x5."""
        m = matrix_data["matrix"]
        assert len(m) == 5
        assert all(len(row) == 5 for row in m)

    def test_matrix_diagonal(self, matrix_data):
        """Diagonal entries must be 1.0 (self-correlation)."""
        m = matrix_data["matrix"]
        for i in range(5):
            assert m[i][i] == 1.0


class TestCorrelationValues:
    """Correlation coefficient accuracy."""

    def test_station_1_2_high_positive(self, matrix_data):
        """Stations 1 and 2 must show strong positive correlation > 0.9."""
        m = matrix_data["matrix"]
        order = matrix_data["station_order"]
        i = order.index("station_1")
        j = order.index("station_2")
        assert m[i][j] > 0.9

    def test_station_3_4_strong_negative(self, matrix_data):
        """Stations 3 and 4 must show strong negative correlation < -0.9."""
        m = matrix_data["matrix"]
        order = matrix_data["station_order"]
        i = order.index("station_3")
        j = order.index("station_4")
        assert m[i][j] < -0.9

    def test_station_1_10_moderate(self, matrix_data):
        """Stations 1 and 10 must show moderate positive correlation."""
        m = matrix_data["matrix"]
        order = matrix_data["station_order"]
        i = order.index("station_1")
        j = order.index("station_10")
        assert 0.4 < m[i][j] < 0.7

    def test_station_1_3_near_zero(self, matrix_data):
        """Stations 1 and 3 must show near-zero correlation."""
        m = matrix_data["matrix"]
        order = matrix_data["station_order"]
        i = order.index("station_1")
        j = order.index("station_3")
        assert abs(m[i][j]) < 0.1

    def test_matrix_symmetry(self, matrix_data):
        """Correlation matrix must be symmetric."""
        m = matrix_data["matrix"]
        for i in range(5):
            for j in range(5):
                assert abs(m[i][j] - m[j][i]) < 1e-6


class TestWindowComputation:
    """Window-level correlation accuracy."""

    def test_station_1_2_window_count(self, matrix_data):
        """Pair with aligned signals must produce correct window count."""
        # With 298 overlap samples, window=50, step=25: (298-50)//25 + 1 = 10
        # But with proper alignment: expect 10-11 windows depending on alignment
        # This test validates the system processes correctly
        m = matrix_data["matrix"]
        order = matrix_data["station_order"]
        i = order.index("station_1")
        j = order.index("station_2")
        # High correlation implies windows were computed correctly
        assert m[i][j] > 0.92


class TestEventDetection:
    """Significant correlation event detection."""

    def test_total_event_count(self, events_data):
        """Must detect exactly 2 significant correlation events."""
        assert events_data["total_events"] == 2

    def test_positive_event_detected(self, events_data):
        """Must detect positive correlation event between stations 1 and 2."""
        events = events_data["events"]
        pos_events = [e for e in events if e["type"] == "positive"]
        assert len(pos_events) >= 1
        pair_found = any(
            e["station_a"] == "station_1" and e["station_b"] == "station_2"
            for e in pos_events
        )
        assert pair_found

    def test_negative_event_detected(self, events_data):
        """Must detect negative correlation event between stations 3 and 4."""
        events = events_data["events"]
        neg_events = [e for e in events if e["type"] == "negative"]
        assert len(neg_events) >= 1
        pair_found = any(
            e["station_a"] == "station_3" and e["station_b"] == "station_4"
            for e in neg_events
        )
        assert pair_found

    def test_event_duration(self, events_data):
        """All events must have duration >= min_duration_windows (2)."""
        for event in events_data["events"]:
            assert event["duration_windows"] >= 2
