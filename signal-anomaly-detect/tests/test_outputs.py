"""Verification tests for signal anomaly detection pipeline."""
import json
import math
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"


@pytest.fixture
def anomalies():
    path = os.path.join(OUTPUT_DIR, "anomalies.json")
    assert os.path.exists(path), "anomalies.json not found"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def summary():
    path = os.path.join(OUTPUT_DIR, "summary.json")
    assert os.path.exists(path), "summary.json not found"
    with open(path) as f:
        return json.load(f)


class TestAnomalyCount:
    """Tests for correct number of anomalies detected."""

    def test_total_anomalies_is_six(self, anomalies):
        assert len(anomalies) == 6, f"Expected 6 anomalies, got {len(anomalies)}"

    def test_summary_total_matches(self, summary):
        assert summary["total_anomalies"] == 6


class TestStationsAffected:
    """Tests for correct station identification."""

    def test_two_stations_affected(self, summary):
        assert len(summary["stations_affected"]) == 2

    def test_east_station_detected(self, summary):
        assert "east" in summary["stations_affected"]

    def test_north_station_detected(self, summary):
        assert "north" in summary["stations_affected"]

    def test_west_station_not_detected(self, anomalies):
        west_anomalies = [a for a in anomalies if a["station"] == "west"]
        assert len(west_anomalies) == 0, "West station should have no anomalies"


class TestEastStation:
    """Tests for east station anomaly details."""

    def test_east_has_three_anomalies(self, anomalies):
        east = [a for a in anomalies if a["station"] == "east"]
        assert len(east) == 3

    def test_east_bands_are_1_2_3(self, anomalies):
        east = [a for a in anomalies if a["station"] == "east"]
        bands = sorted(a["frequency_band"] for a in east)
        assert bands == [1, 2, 3]

    def test_east_max_score(self, anomalies):
        east = [a for a in anomalies if a["station"] == "east"]
        max_score = max(a["score"] for a in east)
        assert math.isclose(max_score, 7.809904, rel_tol=1e-4), \
            f"East max score should be ~7.8099, got {max_score}"


class TestNorthStation:
    """Tests for north station anomaly details."""

    def test_north_has_three_anomalies(self, anomalies):
        north = [a for a in anomalies if a["station"] == "north"]
        assert len(north) == 3

    def test_north_bands_are_1_2_3(self, anomalies):
        north = [a for a in anomalies if a["station"] == "north"]
        bands = sorted(a["frequency_band"] for a in north)
        assert bands == [1, 2, 3]

    def test_north_max_score(self, anomalies):
        north = [a for a in anomalies if a["station"] == "north"]
        max_score = max(a["score"] for a in north)
        assert math.isclose(max_score, 4.695203, rel_tol=1e-4), \
            f"North max score should be ~4.6952, got {max_score}"


class TestSummaryScores:
    """Tests for summary statistics accuracy."""

    def test_max_score_value(self, summary):
        assert math.isclose(summary["max_score"], 7.809904, rel_tol=1e-4), \
            f"Max score should be ~7.8099, got {summary['max_score']}"

    def test_avg_score_value(self, summary):
        assert math.isclose(summary["avg_score"], 6.150096, rel_tol=1e-3), \
            f"Avg score should be ~6.1501, got {summary['avg_score']}"
