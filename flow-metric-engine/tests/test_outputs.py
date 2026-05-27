"""Validation tests for flow metric engine output."""
import hashlib
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
DATA_DIR = "/app/runtime/data"
MATRIX_PATH = os.path.join(OUTPUT_DIR, "traffic_matrix.json")
REPORT_PATH = os.path.join(OUTPUT_DIR, "anomaly_report.json")


def load_matrix():
    """Load the traffic matrix output."""
    with open(MATRIX_PATH, "r") as f:
        return json.load(f)


def load_report():
    """Load the anomaly report output."""
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


def get_data_hash(filename):
    """Compute SHA256 of a data file to detect tampering."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_matrix_file_exists():
    """Traffic matrix output file must be generated."""
    assert os.path.isfile(MATRIX_PATH)


def test_report_file_exists():
    """Anomaly report output file must be generated."""
    assert os.path.isfile(REPORT_PATH)


def test_data_integrity_eth0():
    """Input data file eth0.json must not be modified."""
    h = get_data_hash("eth0.json")
    assert h == "f70cb7635e9a957887b127c6bce12ede7bce069dde3eedf29926cc3adda2c278", f"eth0.json was tampered: {h}"


def test_data_integrity_eth10():
    """Input data file eth10.json must not be modified."""
    h = get_data_hash("eth10.json")
    assert h == "7622ebc7d1bfd8a7f5d618f2fe8ced87779e801cbaa8cbf215383d4ee2f2b1e3", f"eth10.json was tampered: {h}"


def test_matrix_has_required_fields():
    """Matrix output must contain interface_order, count, and summaries."""
    matrix = load_matrix()
    assert "interface_order" in matrix
    assert "count" in matrix
    assert "summaries" in matrix


def test_interface_count():
    """Matrix must include all 5 configured interfaces."""
    matrix = load_matrix()
    assert matrix["count"] == 5


def test_interface_order_numeric():
    """Interfaces must be ordered by numeric suffix, not lexicographic."""
    matrix = load_matrix()
    order = matrix["interface_order"]
    assert order == ["eth0", "eth1", "eth2", "eth10", "eth11"], (
        f"Expected numeric ordering but got {order}"
    )


def test_bandwidth_magnitude():
    """Average bandwidth must be in thousands of bytes/sec range."""
    matrix = load_matrix()
    for entry in matrix["summaries"]:
        bw = entry["avg_bandwidth_bps"]
        assert bw > 1000, (
            f"{entry['interface_id']} avg_bandwidth={bw}, expected > 1000 bytes/s"
        )


def test_eth10_bandwidth_range():
    """eth10 average bandwidth must be between 55000 and 70000 bytes/sec."""
    matrix = load_matrix()
    eth10 = next(s for s in matrix["summaries"] if s["interface_id"] == "eth10")
    assert 55000 < eth10["avg_bandwidth_bps"] < 70000, (
        f"eth10 avg_bandwidth={eth10['avg_bandwidth_bps']}, expected 55000-70000"
    )


def test_eth0_bandwidth_range():
    """eth0 average bandwidth must be between 13000 and 18000 bytes/sec."""
    matrix = load_matrix()
    eth0 = next(s for s in matrix["summaries"] if s["interface_id"] == "eth0")
    assert 13000 < eth0["avg_bandwidth_bps"] < 18000, (
        f"eth0 avg_bandwidth={eth0['avg_bandwidth_bps']}, expected 13000-18000"
    )


def test_eth10_jitter_above_threshold():
    """eth10 average jitter must exceed 18ms (high-jitter interface)."""
    matrix = load_matrix()
    eth10 = next(s for s in matrix["summaries"] if s["interface_id"] == "eth10")
    assert eth10["avg_jitter_ms"] > 18.0, (
        f"eth10 avg_jitter={eth10['avg_jitter_ms']}, expected > 18.0"
    )


def test_eth2_jitter_below_one():
    """eth2 average jitter must be below 1.0ms (low-jitter interface)."""
    matrix = load_matrix()
    eth2 = next(s for s in matrix["summaries"] if s["interface_id"] == "eth2")
    assert eth2["avg_jitter_ms"] < 1.0, (
        f"eth2 avg_jitter={eth2['avg_jitter_ms']}, expected < 1.0"
    )


def test_anomaly_count():
    """Exactly 2 interfaces must be flagged as anomalous."""
    report = load_report()
    assert report["total_anomalies"] == 2, (
        f"Expected 2 anomalies but got {report['total_anomalies']}"
    )


def test_top_anomaly_is_eth10():
    """The highest-scoring anomaly must be eth10."""
    report = load_report()
    assert len(report["anomalies"]) >= 1
    top = report["anomalies"][0]
    assert top["interface_id"] == "eth10", (
        f"Expected top anomaly to be eth10 but got {top['interface_id']}"
    )


def test_eth10_max_score_above_09():
    """eth10 max anomaly score must exceed 0.9."""
    report = load_report()
    eth10 = next(
        (a for a in report["anomalies"] if a["interface_id"] == "eth10"), None
    )
    assert eth10 is not None, "eth10 not found in anomalies"
    assert eth10["max_score"] > 0.9, (
        f"eth10 max_score={eth10['max_score']}, expected > 0.9"
    )


def test_eth11_is_anomalous():
    """eth11 must be flagged as anomalous."""
    report = load_report()
    ifaces = [a["interface_id"] for a in report["anomalies"]]
    assert "eth11" in ifaces, (
        f"eth11 not in anomalies list: {ifaces}"
    )


def test_eth11_score_range():
    """eth11 max anomaly score must be between 0.7 and 0.9."""
    report = load_report()
    eth11 = next(
        (a for a in report["anomalies"] if a["interface_id"] == "eth11"), None
    )
    assert eth11 is not None
    assert 0.7 < eth11["max_score"] < 0.9, (
        f"eth11 max_score={eth11['max_score']}, expected 0.7-0.9"
    )


def test_total_flagged_windows():
    """Total flagged windows across all anomalies must be 362."""
    report = load_report()
    total = sum(a["total_flagged_windows"] for a in report["anomalies"])
    assert total == 362, (
        f"Total flagged windows={total}, expected 362"
    )
