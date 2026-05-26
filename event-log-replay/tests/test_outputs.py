"""Tests for event log replay engine output."""
import json
import os

ANOMALIES_PATH = "/app/runtime/output/anomalies.json"
SUMMARY_PATH = "/app/runtime/output/summary.json"


def load_anomalies():
    with open(ANOMALIES_PATH) as f:
        return json.load(f)


def load_summary():
    with open(SUMMARY_PATH) as f:
        return json.load(f)


def test_anomalies_file_exists():
    """Output anomalies.json must exist."""
    assert os.path.isfile(ANOMALIES_PATH), f"Missing {ANOMALIES_PATH}"


def test_summary_file_exists():
    """Output summary.json must exist."""
    assert os.path.isfile(SUMMARY_PATH), f"Missing {SUMMARY_PATH}"


def test_anomalies_is_list():
    """anomalies.json must be a JSON array."""
    data = load_anomalies()
    assert isinstance(data, list)


def test_anomaly_entry_fields():
    """Each anomaly must have source_node, severity, violation_count, target_nodes."""
    anomalies = load_anomalies()
    assert len(anomalies) > 0, "No anomalies produced"
    required = {"source_node", "severity", "violation_count", "target_nodes"}
    for a in anomalies:
        missing = required - set(a.keys())
        assert not missing, f"Missing fields: {missing}"


def test_total_anomalies():
    """Exactly 1 anomaly should be reported (only node_alpha has true violations)."""
    summary = load_summary()
    assert summary["total_anomalies"] == 1, (
        f"Expected 1 anomaly but got {summary['total_anomalies']}. "
        f"Concurrent events should not be flagged as violations."
    )


def test_nodes_affected():
    """Only 1 node should be affected."""
    summary = load_summary()
    assert summary["nodes_affected"] == 1, (
        f"Expected 1 affected node but got {summary['nodes_affected']}"
    )


def test_total_violations():
    """Exactly 4 causal violations should be detected."""
    summary = load_summary()
    assert summary["total_violations"] == 4, (
        f"Expected 4 violations but got {summary['total_violations']}. "
        f"Check vector clock comparison — concurrent events are not violations."
    )


def test_max_severity():
    """Max severity should be 0.775."""
    summary = load_summary()
    assert abs(summary["max_severity"] - 0.775) < 0.001, (
        f"Expected max_severity=0.775 but got {summary['max_severity']}"
    )


def test_source_node_is_alpha():
    """The only anomaly source should be node_alpha."""
    anomalies = load_anomalies()
    sources = [a["source_node"] for a in anomalies]
    assert sources == ["node_alpha"], (
        f"Expected source=['node_alpha'] but got {sources}"
    )


def test_violation_count():
    """node_alpha anomaly must have violation_count=4."""
    anomalies = load_anomalies()
    alpha = [a for a in anomalies if a["source_node"] == "node_alpha"]
    assert len(alpha) == 1
    assert alpha[0]["violation_count"] == 4, (
        f"Expected 4 violations for node_alpha but got {alpha[0]['violation_count']}"
    )


def test_target_nodes():
    """node_alpha's violations must target only node_beta."""
    anomalies = load_anomalies()
    alpha = [a for a in anomalies if a["source_node"] == "node_alpha"]
    assert alpha[0]["target_nodes"] == ["node_beta"], (
        f"Expected targets=['node_beta'] but got {alpha[0]['target_nodes']}"
    )


def test_severity_below_one():
    """All severity values must be below 1.0 (properly normalized)."""
    anomalies = load_anomalies()
    for a in anomalies:
        assert a["severity"] <= 1.0, (
            f"Severity {a['severity']} exceeds 1.0 — check weight accumulation"
        )


def test_severity_value():
    """node_alpha severity must be exactly 0.775."""
    anomalies = load_anomalies()
    alpha = [a for a in anomalies if a["source_node"] == "node_alpha"]
    assert abs(alpha[0]["severity"] - 0.775) < 0.001, (
        f"Expected severity=0.775 but got {alpha[0]['severity']}"
    )
