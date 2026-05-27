"""Validation tests for fleet telemetry anomaly detection pipeline output."""
import hashlib
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
DATA_DIR = "/app/runtime/data"
ANOMALIES_PATH = os.path.join(OUTPUT_DIR, "anomalies.json")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "summary.json")


def load_anomalies():
    """Load anomalies output file."""
    with open(ANOMALIES_PATH, "r") as f:
        return json.load(f)


def load_summary():
    """Load summary output file."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def test_data_integrity():
    """Input data files must not be modified from their original state."""
    expected_hashes = {
        "V200.jsonl": "f59c112dc07ff25d49a91a5010e70c978076dc7addb67d442d95fe4d601527d7",
        "V201.jsonl": "b7afac204049c4230a5b58b441f1fd4e7d28e756e45e5d86a76694cc10f39042",
        "V202.jsonl": "4fae4a265de2e13ce6fc9b6bf6123449a25080788ebd6456b7922169fcf42481",
        "V203.jsonl": "b08655bb353a632be1839afdf80180766c68f57da1098f6140f53d4f38281252",
    }
    for fname, expected_hash in expected_hashes.items():
        path = os.path.join(DATA_DIR, fname)
        assert os.path.isfile(path), f"Data file {fname} must exist"
        with open(path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        assert actual_hash == expected_hash, (
            f"Data file {fname} has been modified (hash mismatch)"
        )


def test_anomalies_file_exists():
    """Anomalies output file must be generated at the expected path."""
    assert os.path.isfile(ANOMALIES_PATH), "anomalies.json not found"


def test_summary_file_exists():
    """Summary output file must be generated at the expected path."""
    assert os.path.isfile(SUMMARY_PATH), "summary.json not found"


def test_anomalies_is_list():
    """Anomalies output must be a JSON array."""
    anomalies = load_anomalies()
    assert isinstance(anomalies, list)


def test_anomaly_entry_fields():
    """Each anomaly entry must contain all required fields."""
    anomalies = load_anomalies()
    required = {"vehicle_id", "window_start", "window_end", "fused_score",
                "severity", "sensors_reporting"}
    for entry in anomalies:
        assert required.issubset(entry.keys()), (
            f"Missing fields in anomaly entry: {required - set(entry.keys())}"
        )


def test_total_anomalies_count():
    """Pipeline must detect exactly 11 anomalies across the fleet."""
    summary = load_summary()
    assert summary["total_anomalies"] == 11, (
        f"Expected 11 total anomalies but got {summary['total_anomalies']}"
    )


def test_vehicles_affected_count():
    """All 4 vehicles in the fleet must have at least one anomaly."""
    summary = load_summary()
    assert summary["vehicles_affected"] == 4, (
        f"Expected 4 vehicles affected but got {summary['vehicles_affected']}"
    )


def test_severity_emergency_count():
    """Pipeline must classify exactly 4 anomalies as emergency severity."""
    summary = load_summary()
    assert summary["severity_counts"]["emergency"] == 4, (
        f"Expected 4 emergency anomalies but got "
        f"{summary['severity_counts']['emergency']}"
    )


def test_severity_critical_count():
    """Pipeline must classify exactly 2 anomalies as critical severity."""
    summary = load_summary()
    assert summary["severity_counts"]["critical"] == 2, (
        f"Expected 2 critical anomalies but got "
        f"{summary['severity_counts']['critical']}"
    )


def test_severity_warning_count():
    """Pipeline must classify exactly 5 anomalies as warning severity."""
    summary = load_summary()
    assert summary["severity_counts"]["warning"] == 5, (
        f"Expected 5 warning anomalies but got "
        f"{summary['severity_counts']['warning']}"
    )


def test_max_fused_score():
    """Maximum fused anomaly score must be approximately 59.01."""
    summary = load_summary()
    assert abs(summary["max_fused_score"] - 59.0067) < 0.05, (
        f"Expected max_fused_score near 59.0067 but got "
        f"{summary['max_fused_score']}"
    )


def test_avg_fused_score():
    """Average fused score across all anomalies must be approximately 10.18."""
    summary = load_summary()
    assert abs(summary["avg_fused_score"] - 10.1757) < 0.05, (
        f"Expected avg_fused_score near 10.1757 but got "
        f"{summary['avg_fused_score']}"
    )


def test_v200_highest_severity():
    """Vehicle V200 must have its highest anomaly classified as emergency."""
    anomalies = load_anomalies()
    v200 = [a for a in anomalies if a["vehicle_id"] == "V200"]
    assert len(v200) >= 1, "V200 must have at least one anomaly"
    severities = [a["severity"] for a in v200]
    assert "emergency" in severities, (
        f"V200 should have at least one emergency but got: {severities}"
    )


def test_v200_emergency_score():
    """V200 emergency anomaly fused score must be approximately 13.0."""
    anomalies = load_anomalies()
    v200_emerg = [a for a in anomalies
                  if a["vehicle_id"] == "V200" and a["severity"] == "emergency"]
    assert len(v200_emerg) == 1, "V200 must have exactly one emergency"
    assert abs(v200_emerg[0]["fused_score"] - 12.9955) < 0.1, (
        f"V200 emergency score should be ~12.9955 but got "
        f"{v200_emerg[0]['fused_score']}"
    )


def test_v203_has_highest_score():
    """Vehicle V203 must contain the fleet-wide maximum anomaly score."""
    anomalies = load_anomalies()
    max_entry = max(anomalies, key=lambda a: a["fused_score"])
    assert max_entry["vehicle_id"] == "V203", (
        f"V203 should have highest score but {max_entry['vehicle_id']} does"
    )


def test_v201_all_warnings():
    """All anomalies for vehicle V201 must be warning severity only."""
    anomalies = load_anomalies()
    v201 = [a for a in anomalies if a["vehicle_id"] == "V201"]
    assert len(v201) == 3, f"V201 should have 3 anomalies but got {len(v201)}"
    for a in v201:
        assert a["severity"] == "warning", (
            f"V201 anomaly at ts={a['window_start']} has severity "
            f"'{a['severity']}' but should be 'warning'"
        )


def test_window_end_values():
    """All anomaly window_end values must equal window_start + 15."""
    anomalies = load_anomalies()
    for a in anomalies:
        expected_end = a["window_start"] + 15
        assert a["window_end"] == expected_end, (
            f"Anomaly at ts={a['window_start']} has window_end={a['window_end']} "
            f"but expected {expected_end}"
        )


def test_window_boundaries_aligned():
    """All anomaly window_start values must align to 15-second boundaries from 1000."""
    anomalies = load_anomalies()
    for a in anomalies:
        offset = (a["window_start"] - 1000) % 15
        assert offset == 0, (
            f"Window start {a['window_start']} not aligned to 15s boundary"
        )


def test_v202_anomaly_count():
    """Vehicle V202 must have exactly 2 anomalies detected."""
    anomalies = load_anomalies()
    v202 = [a for a in anomalies if a["vehicle_id"] == "V202"]
    assert len(v202) == 2, (
        f"V202 should have 2 anomalies but got {len(v202)}"
    )


def test_v202_both_emergency():
    """Both V202 anomalies must be classified as emergency severity."""
    anomalies = load_anomalies()
    v202 = [a for a in anomalies if a["vehicle_id"] == "V202"]
    assert len(v202) == 2
    for a in v202:
        assert a["severity"] == "emergency", (
            f"V202 anomaly at ts={a['window_start']} has severity "
            f"'{a['severity']}' but should be 'emergency'"
        )
