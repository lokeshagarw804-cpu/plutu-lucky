"""Validation tests for fleet telemetry engine output."""
import hashlib
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
DATA_DIR = "/app/runtime/data"
REPORT_PATH = os.path.join(OUTPUT_DIR, "report.json")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "summary.json")


def load_report():
    """Load report output."""
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


def load_summary():
    """Load summary output."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def _hash_file(path):
    """Compute SHA256 of a data file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def test_data_integrity_v1():
    """Input data for V1 must not be modified."""
    h = _hash_file(os.path.join(DATA_DIR, "V1.json"))
    assert h == "4372757f86ae16f7011f41213ea99ea34321412eae5b5c6348ac4f0326ed0841"


def test_data_integrity_v3():
    """Input data for V3 must not be modified."""
    h = _hash_file(os.path.join(DATA_DIR, "V3.json"))
    assert h == "d975d15780b74ec71516e167ba3d7ed9f4dfa789e2d41fdb4ecfc6b7218cc858"


def test_report_file_exists():
    """Report output file must be generated at expected path."""
    assert os.path.isfile(REPORT_PATH)


def test_summary_file_exists():
    """Summary output file must be generated at expected path."""
    assert os.path.isfile(SUMMARY_PATH)


def test_report_has_vehicle_order():
    """Report must contain vehicle_order field."""
    report = load_report()
    assert "vehicle_order" in report
    assert isinstance(report["vehicle_order"], list)


def test_report_has_vehicles():
    """Report must contain vehicles list."""
    report = load_report()
    assert "vehicles" in report
    assert isinstance(report["vehicles"], list)


def test_summary_has_required_fields():
    """Summary must contain all required aggregate fields."""
    summary = load_summary()
    required = ["total_trips", "total_distance_km", "total_fuel_liters",
                "fleet_efficiency_km_per_liter", "max_driver_score", "best_vehicle"]
    for field in required:
        assert field in summary, f"Missing field: {field}"


def test_total_trips_count():
    """Fleet must have exactly 7 total trips across all vehicles."""
    summary = load_summary()
    assert summary["total_trips"] == 7, (
        f"Expected 7 total trips but got {summary['total_trips']}"
    )


def test_total_distance():
    """Total fleet distance must be approximately 70.14 km."""
    summary = load_summary()
    assert abs(summary["total_distance_km"] - 70.14) < 0.5, (
        f"Expected ~70.14 km but got {summary['total_distance_km']}"
    )


def test_total_fuel():
    """Total fleet fuel consumption must be approximately 11.48 liters."""
    summary = load_summary()
    assert abs(summary["total_fuel_liters"] - 11.48) < 0.1, (
        f"Expected ~11.48 L but got {summary['total_fuel_liters']}"
    )


def test_vehicle_order_numeric():
    """Vehicles must be ordered by numeric identifier not lexicographic."""
    report = load_report()
    assert report["vehicle_order"] == ["V1", "V2", "V3", "V10", "V12"], (
        f"Expected [V1, V2, V3, V10, V12] but got {report['vehicle_order']}"
    )


def test_best_vehicle():
    """V3 must have the highest driver score."""
    summary = load_summary()
    assert summary["best_vehicle"] == "V3", (
        f"Expected best_vehicle=V3 but got {summary['best_vehicle']}"
    )


def test_v3_driver_score():
    """V3 driver score must be approximately 0.87."""
    report = load_report()
    v3 = [v for v in report["vehicles"] if v["vehicle_id"] == "V3"]
    assert len(v3) == 1
    assert abs(v3[0]["driver_score"] - 0.8701) < 0.005, (
        f"Expected V3 score ~0.8701 but got {v3[0]['driver_score']}"
    )


def test_v10_driver_score_not_deflated():
    """V10 score must use applicable weights only (no speed data available)."""
    report = load_report()
    v10 = [v for v in report["vehicles"] if v["vehicle_id"] == "V10"]
    assert len(v10) == 1
    # V10 has no speed data; correct score uses only efficiency+idle weights
    # Buggy code divides by all 3 weights, deflating the score
    assert v10[0]["driver_score"] > 0.55, (
        f"V10 score too low ({v10[0]['driver_score']}), denominator may be wrong"
    )


def test_v1_trip_count():
    """V1 must have exactly 2 trips (330s gap exceeds 300s threshold)."""
    report = load_report()
    v1 = [v for v in report["vehicles"] if v["vehicle_id"] == "V1"]
    assert len(v1) == 1
    assert v1[0]["trips"] == 2, (
        f"Expected V1 trips=2 but got {v1[0]['trips']}"
    )


def test_v2_trip_count():
    """V2 must have exactly 1 trip (300s gap equals threshold, not exceeded)."""
    report = load_report()
    v2 = [v for v in report["vehicles"] if v["vehicle_id"] == "V2"]
    assert len(v2) == 1
    assert v2[0]["trips"] == 1, (
        f"Expected V2 trips=1 but got {v2[0]['trips']}"
    )


def test_v1_distance():
    """V1 total distance must be approximately 17.92 km."""
    report = load_report()
    v1 = [v for v in report["vehicles"] if v["vehicle_id"] == "V1"]
    assert len(v1) == 1
    assert abs(v1[0]["distance_km"] - 17.92) < 0.3, (
        f"Expected V1 distance ~17.92 km but got {v1[0]['distance_km']}"
    )


def test_v1_fuel():
    """V1 total fuel must be approximately 2.94 liters."""
    report = load_report()
    v1 = [v for v in report["vehicles"] if v["vehicle_id"] == "V1"]
    assert len(v1) == 1
    assert abs(v1[0]["fuel_liters"] - 2.94) < 0.05, (
        f"Expected V1 fuel ~2.94 L but got {v1[0]['fuel_liters']}"
    )


def test_v2_fuel():
    """V2 total fuel must be approximately 2.82 liters (single trip accumulation)."""
    report = load_report()
    v2 = [v for v in report["vehicles"] if v["vehicle_id"] == "V2"]
    assert len(v2) == 1
    assert abs(v2[0]["fuel_liters"] - 2.82) < 0.05, (
        f"Expected V2 fuel ~2.82 L but got {v2[0]['fuel_liters']}"
    )


def test_max_driver_score_bounded():
    """Maximum driver score must be between 0 and 1."""
    summary = load_summary()
    assert 0 < summary["max_driver_score"] <= 1.0


def test_fleet_efficiency():
    """Fleet efficiency must be approximately 6.11 km/L."""
    summary = load_summary()
    assert abs(summary["fleet_efficiency_km_per_liter"] - 6.11) < 0.15, (
        f"Expected fleet efficiency ~6.11 but got {summary['fleet_efficiency_km_per_liter']}"
    )
