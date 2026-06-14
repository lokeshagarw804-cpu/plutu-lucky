"""Verification tests for event-log-replay pipeline output."""
import json
import os
import pytest


OUTPUT_DIR = "/app/runtime/output"


@pytest.fixture
def anomalies():
    path = os.path.join(OUTPUT_DIR, "anomalies.json")
    assert os.path.exists(path), f"Missing output file: {path}"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def summary():
    path = os.path.join(OUTPUT_DIR, "summary.json")
    assert os.path.exists(path), f"Missing output file: {path}"
    with open(path) as f:
        return json.load(f)


class TestSummary:
    def test_total_violations(self, summary):
        assert summary["total_violations"] == 3

    def test_total_anomalies(self, summary):
        assert summary["total_anomalies"] == 1

    def test_nodes_affected(self, summary):
        assert summary["nodes_affected"] == 1

    def test_max_severity(self, summary):
        assert abs(summary["max_severity"] - 0.513) < 0.001


class TestAnomalies:
    def test_anomaly_count(self, anomalies):
        assert len(anomalies) == 1

    def test_source_node(self, anomalies):
        assert anomalies[0]["source_node"] == "node_alpha"

    def test_severity_value(self, anomalies):
        assert abs(anomalies[0]["severity"] - 0.513) < 0.001

    def test_violation_count(self, anomalies):
        assert anomalies[0]["violation_count"] == 3

    def test_target_nodes(self, anomalies):
        assert anomalies[0]["target_nodes"] == ["node_beta"]

    def test_no_gamma_in_targets(self, anomalies):
        for a in anomalies:
            assert "node_gamma" not in a["target_nodes"]

    def test_no_beta_source(self, anomalies):
        sources = [a["source_node"] for a in anomalies]
        assert "node_beta" not in sources

    def test_severity_below_one(self, anomalies):
        for a in anomalies:
            assert a["severity"] <= 1.0

    def test_anomaly_has_required_fields(self, anomalies):
        required = {"source_node", "severity", "violation_count", "target_nodes"}
        for a in anomalies:
            assert required.issubset(set(a.keys()))


class TestSummaryFields:
    def test_summary_has_required_fields(self, summary):
        required = {"total_anomalies", "nodes_affected", "total_violations", "max_severity"}
        assert required.issubset(set(summary.keys()))

    def test_max_severity_matches_anomalies(self, anomalies, summary):
        if anomalies:
            max_sev = max(a["severity"] for a in anomalies)
            assert abs(summary["max_severity"] - max_sev) < 0.0001

    def test_total_anomalies_matches_list(self, anomalies, summary):
        assert summary["total_anomalies"] == len(anomalies)
