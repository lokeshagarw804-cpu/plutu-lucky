"""Tests for geofence alert engine output correctness."""
import json
import os

ALERTS_PATH = "/app/runtime/output/alerts.json"
SUMMARY_PATH = "/app/runtime/output/summary.json"


def load_alerts():
    with open(ALERTS_PATH, "r") as f:
        return json.load(f)


def load_summary():
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def test_alerts_file_exists():
    """Output file alerts.json must be created."""
    assert os.path.isfile(ALERTS_PATH), f"Missing: {ALERTS_PATH}"


def test_summary_file_exists():
    """Output file summary.json must be created."""
    assert os.path.isfile(SUMMARY_PATH), f"Missing: {SUMMARY_PATH}"


def test_alerts_is_list():
    """alerts.json must contain a JSON array."""
    alerts = load_alerts()
    assert isinstance(alerts, list), "alerts.json must be a list"


def test_alert_entry_fields():
    """Each alert must have zone_id, vehicle_id, severity, dwell_seconds, readings_inside."""
    alerts = load_alerts()
    assert len(alerts) > 0, "No alerts generated"
    required = {"zone_id", "vehicle_id", "severity", "dwell_seconds", "readings_inside"}
    for alert in alerts:
        missing = required - set(alert.keys())
        assert not missing, f"Alert missing fields: {missing}"


def test_total_alerts_count():
    """System must produce exactly 9 alerts across all zones."""
    summary = load_summary()
    assert summary["total_alerts"] == 9, (
        f"Expected 9 total alerts but got {summary['total_alerts']}"
    )


def test_zones_violated_count():
    """All 3 geofence zones must have at least one violation."""
    summary = load_summary()
    assert summary["zones_violated"] == 3, (
        f"Expected 3 zones violated but got {summary['zones_violated']}"
    )


def test_total_dwell_sum():
    """Sum of all dwell_seconds across alerts must be 1765."""
    summary = load_summary()
    assert summary["total_dwell"] == 1765, (
        f"Expected total_dwell=1765 but got {summary['total_dwell']}"
    )


def test_max_severity_bounded():
    """Maximum severity must not exceed 1.0 (weighted average is normalized)."""
    summary = load_summary()
    assert summary["max_severity"] <= 1.0, (
        f"max_severity={summary['max_severity']} exceeds 1.0 — "
        f"check weight accumulation in alert severity computation"
    )


def test_max_severity_value():
    """Maximum severity across all alerts must be 0.7769."""
    summary = load_summary()
    assert abs(summary["max_severity"] - 0.7769) < 0.001, (
        f"Expected max_severity=0.7769 but got {summary['max_severity']}"
    )


def test_zone_beta_severity_uniform():
    """All zone_beta alerts must have severity exactly 0.5."""
    alerts = load_alerts()
    beta_alerts = [a for a in alerts if a["zone_id"] == "zone_beta"]
    assert len(beta_alerts) == 3, f"Expected 3 zone_beta alerts, got {len(beta_alerts)}"
    for alert in beta_alerts:
        assert alert["severity"] == 0.5, (
            f"zone_beta alert for {alert['vehicle_id']} has severity "
            f"{alert['severity']}, expected 0.5"
        )


def test_zone_beta_deterministic_order():
    """zone_beta alerts with equal severity must be sorted by vehicle_id."""
    alerts = load_alerts()
    beta_alerts = [a for a in alerts if a["zone_id"] == "zone_beta"]
    vehicle_ids = [a["vehicle_id"] for a in beta_alerts]
    assert vehicle_ids == ["V102", "V203", "V302"], (
        f"zone_beta ordering should be ['V102', 'V203', 'V302'] but got {vehicle_ids}"
    )


def test_zone_alpha_first_vehicle():
    """Highest severity alert in zone_alpha must be vehicle V301."""
    alerts = load_alerts()
    alpha_alerts = [a for a in alerts if a["zone_id"] == "zone_alpha"]
    assert len(alpha_alerts) >= 1
    assert alpha_alerts[0]["vehicle_id"] == "V301", (
        f"First zone_alpha alert should be V301 (highest severity) "
        f"but got {alpha_alerts[0]['vehicle_id']}"
    )


def test_v101_zone_alpha_dwell():
    """Vehicle V101 dwell in zone_alpha must be 265 seconds."""
    alerts = load_alerts()
    v101_alpha = [a for a in alerts if a["vehicle_id"] == "V101" and a["zone_id"] == "zone_alpha"]
    assert len(v101_alpha) == 1, "V101 must have exactly one zone_alpha alert"
    assert v101_alpha[0]["dwell_seconds"] == 265, (
        f"V101 zone_alpha dwell should be 265s but got {v101_alpha[0]['dwell_seconds']}"
    )


def test_v101_zone_alpha_readings():
    """Vehicle V101 must have 9 confirmed readings inside zone_alpha."""
    alerts = load_alerts()
    v101_alpha = [a for a in alerts if a["vehicle_id"] == "V101" and a["zone_id"] == "zone_alpha"]
    assert len(v101_alpha) == 1
    assert v101_alpha[0]["readings_inside"] == 9, (
        f"V101 zone_alpha readings_inside should be 9 but got "
        f"{v101_alpha[0]['readings_inside']}"
    )
