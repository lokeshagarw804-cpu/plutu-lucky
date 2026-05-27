"""Validation tests for fleet telemetry monitor output."""
import hashlib
import json
import os


OUTPUT_DIR = "/app/runtime/output"
DATA_DIR = "/app/runtime/data"
ALERTS_PATH = os.path.join(OUTPUT_DIR, "alerts.json")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "summary.json")


def load_alerts():
    """Load alerts output file."""
    with open(ALERTS_PATH, "r") as f:
        return json.load(f)


def load_summary():
    """Load summary output file."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def compute_data_hash(filename):
    """Compute SHA256 hash of a data file to verify integrity."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_alerts_file_exists():
    """Alert output file must be generated at the expected path."""
    assert os.path.isfile(ALERTS_PATH)


def test_summary_file_exists():
    """Summary output file must be generated at the expected path."""
    assert os.path.isfile(SUMMARY_PATH)


def test_data_integrity_truck_1():
    """Data file for truck_1 must not be modified."""
    h = compute_data_hash("truck_1.json")
    assert h == "354622b312c6f798578621c416a27ebb67cfbdfc6b048e8458a708326c135018", (
        "truck_1.json has been tampered with"
    )


def test_data_integrity_truck_3():
    """Data file for truck_3 must not be modified."""
    h = compute_data_hash("truck_3.json")
    assert h == "bddf8ff15c9cac3f8e3fe9a66fa63bb9930ef7038ed6cb6e3570616d5053d66a", (
        "truck_3.json has been tampered with"
    )


def test_alerts_is_list():
    """Alerts output must be a JSON array."""
    alerts = load_alerts()
    assert isinstance(alerts, list)


def test_alert_entry_fields():
    """Each alert must contain all required fields."""
    alerts = load_alerts()
    required = {"vehicle_id", "start_window", "end_window", "duration_windows",
                "total_speed_spikes", "max_fuel_consumption",
                "max_thermal_deviation", "severity"}
    for alert in alerts:
        assert required.issubset(alert.keys()), (
            f"Alert missing fields: {required - set(alert.keys())}"
        )


def test_total_alerts_count():
    """System must produce exactly 7 alerts total."""
    summary = load_summary()
    assert summary["total_alerts"] == 7, (
        f"Expected 7 alerts but got {summary['total_alerts']}"
    )


def test_vehicles_affected_count():
    """Exactly 4 vehicles must have alerts."""
    summary = load_summary()
    assert summary["vehicles_affected"] == 4, (
        f"Expected 4 vehicles affected but got {summary['vehicles_affected']}"
    )


def test_total_duration_sum():
    """Total duration across all alerts must be 17 windows."""
    summary = load_summary()
    assert summary["total_duration_windows"] == 17, (
        f"Expected total_duration=17 but got {summary['total_duration_windows']}"
    )


def test_total_speed_spikes():
    """Total speed spikes across all alerts must be 54."""
    summary = load_summary()
    assert summary["total_speed_spikes"] == 54, (
        f"Expected total_speed_spikes=54 but got {summary['total_speed_spikes']}"
    )


def test_max_severity_bounded():
    """Maximum severity must not exceed the configured cap of 1.0."""
    summary = load_summary()
    assert summary["max_severity"] <= 1.0


def test_max_severity_value():
    """Maximum severity across all alerts must be 0.5834."""
    summary = load_summary()
    assert abs(summary["max_severity"] - 0.5834) < 0.001, (
        f"Expected max_severity=0.5834 but got {summary['max_severity']}"
    )


def test_vehicle_order_numeric():
    """Vehicles must be ordered numerically by identifier suffix."""
    summary = load_summary()
    assert summary["vehicle_order"] == ["truck_1", "truck_3", "truck_7", "truck_12"], (
        f"Expected numeric order [truck_1, truck_3, truck_7, truck_12] "
        f"but got {summary['vehicle_order']}"
    )


def test_truck_1_alert_count():
    """Truck 1 must produce exactly 2 alerts."""
    alerts = load_alerts()
    t1_alerts = [a for a in alerts if a["vehicle_id"] == "truck_1"]
    assert len(t1_alerts) == 2, (
        f"Expected 2 alerts for truck_1 but got {len(t1_alerts)}"
    )


def test_truck_1_first_alert_severity():
    """Truck 1 highest severity alert must be 0.5492."""
    alerts = load_alerts()
    t1_alerts = [a for a in alerts if a["vehicle_id"] == "truck_1"]
    assert len(t1_alerts) >= 1
    assert abs(t1_alerts[0]["severity"] - 0.5492) < 0.001, (
        f"truck_1 first alert severity should be 0.5492 but got "
        f"{t1_alerts[0]['severity']}"
    )


def test_truck_3_highest_severity_alert():
    """Truck 3 highest severity alert must have 8 speed spikes."""
    alerts = load_alerts()
    t3_alerts = [a for a in alerts if a["vehicle_id"] == "truck_3"]
    assert len(t3_alerts) >= 1
    assert t3_alerts[0]["total_speed_spikes"] == 8, (
        f"truck_3 highest severity alert should have 8 spikes "
        f"but got {t3_alerts[0]['total_speed_spikes']}"
    )


def test_truck_7_single_alert_duration():
    """Truck 7 must have exactly 1 alert with duration 2 windows."""
    alerts = load_alerts()
    t7_alerts = [a for a in alerts if a["vehicle_id"] == "truck_7"]
    assert len(t7_alerts) == 1, (
        f"Expected 1 alert for truck_7 but got {len(t7_alerts)}"
    )
    assert t7_alerts[0]["duration_windows"] == 2, (
        f"truck_7 alert duration should be 2 but got "
        f"{t7_alerts[0]['duration_windows']}"
    )


def test_truck_12_max_fuel_consumption():
    """Truck 12 highest fuel consumption alert must show 8.4."""
    alerts = load_alerts()
    t12_alerts = [a for a in alerts if a["vehicle_id"] == "truck_12"]
    assert len(t12_alerts) >= 1
    max_fuel = max(a["max_fuel_consumption"] for a in t12_alerts)
    assert abs(max_fuel - 8.4) < 0.01, (
        f"truck_12 max fuel consumption should be 8.4 but got {max_fuel}"
    )
