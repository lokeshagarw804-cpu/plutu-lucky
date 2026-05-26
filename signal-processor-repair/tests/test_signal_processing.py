"""
Tests for the signal processing system.

Validates calibration accuracy, correlation bounds,
anomaly detection sensitivity, and output ordering.
"""
import json
import os
import pytest


ANOMALY_PATH = "/app/runtime/output/anomaly_report.json"
CORRELATION_PATH = "/app/runtime/output/correlation_matrix.json"
SUMMARY_PATH = "/app/runtime/output/processing_summary.json"


def load_anomaly_report():
    """Load the anomaly report output."""
    with open(ANOMALY_PATH, "r") as f:
        return json.load(f)


def load_correlation_matrix():
    """Load the correlation matrix output."""
    with open(CORRELATION_PATH, "r") as f:
        return json.load(f)


def load_summary():
    """Load the processing summary output."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


# --- EASY TESTS (always pass with buggy code) ---

class TestOutputStructure:
    """Verify basic output file existence and structure."""

    def test_anomaly_report_exists(self):
        """Output anomaly report must be present."""
        assert os.path.isfile(ANOMALY_PATH), (
            "Anomaly report not found"
        )

    def test_correlation_matrix_exists(self):
        """Output correlation matrix must be present."""
        assert os.path.isfile(CORRELATION_PATH), (
            "Correlation matrix not found"
        )

    def test_summary_exists(self):
        """Output processing summary must be present."""
        assert os.path.isfile(SUMMARY_PATH), (
            "Processing summary not found"
        )

    def test_summary_required_fields(self):
        """Summary must contain expected top-level fields."""
        summary = load_summary()
        required = [
            "total_readings", "stations_processed", "channels",
            "windows_created", "total_anomalies", "correlation_pairs",
            "anomalies_by_station"
        ]
        for field in required:
            assert field in summary, f"Missing field: {field}"


# --- MEDIUM TESTS (require Bug A or Bug E individually) ---

class TestCalibration:
    """Verify station calibration correctness."""

    def test_all_stations_processed(self):
        """All four stations must appear in processed output."""
        summary = load_summary()
        stations = summary["stations_processed"]
        assert len(stations) == 4, (
            f"Expected 4 stations processed, got {len(stations)}"
        )

    def test_total_reading_count(self):
        """All 56 readings from 4 station files must be calibrated."""
        summary = load_summary()
        assert summary["total_readings"] == 56, (
            f"Expected 56 calibrated readings, got {summary['total_readings']}"
        )

    def test_calibration_values_physical_range(self):
        """Calibrated pressure values must remain in physical range (90-110).

        Raw pressure readings are approximately 98-104 hPa. After applying
        the station calibration offset, values should remain within a
        plausible range for atmospheric pressure measurements.
        """
        report = load_anomaly_report()
        entries = report["entries"]
        pressure_entries = [
            e for e in entries if e["channel"] == "pressure"
        ]
        if not pressure_entries:
            pytest.skip("No pressure anomalies to verify")
        for entry in pressure_entries:
            assert 90.0 <= entry["calibrated_value"] <= 110.0, (
                f"Reading {entry['reading_id']} has calibrated_value="
                f"{entry['calibrated_value']} outside physical range"
            )


# --- MEDIUM-HARD TESTS (require multiple bug fixes) ---

class TestAnomalyDetection:
    """Verify anomaly detection accuracy."""

    def test_anomaly_count(self):
        """Expected 96 anomalies with correct calibration and threshold."""
        report = load_anomaly_report()
        assert report["total_anomalies"] == 96, (
            f"Expected 96 anomalies, got {report['total_anomalies']}"
        )

    def test_delta_station_has_anomalies(self):
        """The delta station must have detected anomalies."""
        summary = load_summary()
        by_station = summary["anomalies_by_station"]
        assert "delta" in by_station and by_station["delta"] > 0, (
            "Delta station should have anomalies in the output"
        )

    def test_anomaly_severity_values(self):
        """Severity scores must reflect correct deviation ratios.

        With the proper detection threshold, severity = deviation / threshold.
        All severities should exceed 1.0 (since only readings above
        threshold are flagged) and the maximum should not exceed 15.0
        for this dataset.
        """
        report = load_anomaly_report()
        entries = report["entries"]
        assert len(entries) > 0, "No anomaly entries found"
        for entry in entries:
            assert entry["severity_score"] > 1.0, (
                f"Severity {entry['severity_score']} should exceed 1.0"
            )
            assert entry["severity_score"] < 15.0, (
                f"Severity {entry['severity_score']} exceeds expected maximum"
            )


# --- HARD TESTS (require 3+ bug fixes together) ---

class TestCorrelationBounds:
    """Verify correlation coefficient mathematical properties."""

    def test_correlation_values_bounded(self):
        """All average correlation coefficients must be in [-1.0, 1.0].

        Pearson correlation is mathematically bounded. Values outside this
        range indicate a computation error in the correlation accumulation
        logic.
        """
        matrix = load_correlation_matrix()
        entries = matrix["entries"]
        assert len(entries) > 0, "No correlation entries found"
        for entry in entries:
            assert -1.0 <= entry["avg_correlation"] <= 1.0, (
                f"Pair {entry['pair']} has avg_correlation="
                f"{entry['avg_correlation']} outside valid range [-1, 1]"
            )

    def test_correlation_pair_count(self):
        """Expected 6 correlation pairs with all 4 stations included.

        With 4 stations, there are C(4,2) = 6 possible pairs on the
        pressure channel.
        """
        matrix = load_correlation_matrix()
        assert matrix["total_pairs"] == 6, (
            f"Expected 6 correlation pairs, got {matrix['total_pairs']}"
        )


class TestDeterministicOrdering:
    """Verify deterministic anomaly report ordering."""

    def test_anomaly_sort_stability(self):
        """Anomalies with equal severity must be ordered by station then time.

        When multiple anomalies share the same severity score, the output
        must be deterministic. Entries at equal severity are ordered by
        station_id (ascending) then timestamp (ascending).
        """
        report = load_anomaly_report()
        entries = report["entries"]
        for i in range(len(entries) - 1):
            curr = entries[i]
            nxt = entries[i + 1]
            if curr["severity_score"] == nxt["severity_score"]:
                curr_key = (curr["station_id"], curr["timestamp"])
                nxt_key = (nxt["station_id"], nxt["timestamp"])
                assert curr_key <= nxt_key, (
                    f"At position {i}, entries with severity="
                    f"{curr['severity_score']} are not properly ordered: "
                    f"({curr['station_id']}, {curr['timestamp']}) should "
                    f"come before ({nxt['station_id']}, {nxt['timestamp']})"
                )

    def test_anomaly_descending_severity(self):
        """Anomalies must be sorted by severity in descending order."""
        report = load_anomaly_report()
        entries = report["entries"]
        for i in range(len(entries) - 1):
            assert entries[i]["severity_score"] >= entries[i + 1]["severity_score"], (
                f"Entries not in descending severity order at position {i}"
            )
