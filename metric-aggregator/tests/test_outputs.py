"""Validation tests for metric aggregation engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
REPORT_PATH = os.path.join(OUTPUT_DIR, "health_report.json")


@pytest.fixture(scope="module")
def report():
    """Load health report output."""
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def summary(report):
    return report["summary"]


@pytest.fixture(scope="module")
def incidents(report):
    return report["incidents"]


@pytest.fixture(scope="module")
def node_details(report):
    return report["node_details"]


class TestSummary:
    """Overall health summary validation."""

    def test_total_incidents(self, summary):
        assert summary["total_incidents"] == 3

    def test_nodes_affected(self, summary):
        assert summary["nodes_affected"] == 3

    def test_max_severity(self, summary):
        assert abs(summary["max_severity"] - 1.0) < 0.001

    def test_total_degraded_windows(self, summary):
        assert summary["total_degraded_windows"] == 16

    def test_worst_node(self, summary):
        assert summary["worst_node"] == "service_api"


class TestIncidents:
    """Incident detection validation."""

    def test_incident_count(self, incidents):
        assert len(incidents) == 3

    def test_api_incident(self, incidents):
        api_incs = [i for i in incidents if i["node_id"] == "service_api"]
        assert len(api_incs) == 1
        assert api_incs[0]["duration_windows"] == 8
        assert abs(api_incs[0]["severity"] - 1.0) < 0.001

    def test_worker_incident(self, incidents):
        worker_incs = [i for i in incidents if i["node_id"] == "service_worker"]
        assert len(worker_incs) == 1
        assert worker_incs[0]["duration_windows"] == 3
        assert abs(worker_incs[0]["peak_score"] - 0.6667) < 0.001

    def test_gateway_incident(self, incidents):
        gw_incs = [i for i in incidents if i["node_id"] == "service_gateway"]
        assert len(gw_incs) == 1
        assert gw_incs[0]["duration_windows"] == 5
        assert abs(gw_incs[0]["severity"] - 0.8215) < 0.001

    def test_no_cache_incident(self, incidents):
        cache_incs = [i for i in incidents if i["node_id"] == "service_cache"]
        assert len(cache_incs) == 0


class TestNodeDetails:
    """Per-node health detail validation."""

    def test_node_count_and_presence(self, node_details):
        assert len(node_details) == 4
        node_ids = [n["node_id"] for n in node_details]
        assert "service_api" in node_ids
        assert "service_worker" in node_ids
        assert "service_gateway" in node_ids
        assert "service_cache" in node_ids

    def test_api_avg_percentile(self, node_details):
        api = [n for n in node_details if n["node_id"] == "service_api"][0]
        assert abs(api["avg_percentile"] - 1.0) < 0.001

    def test_cache_avg_percentile(self, node_details):
        cache = [n for n in node_details if n["node_id"] == "service_cache"][0]
        assert abs(cache["avg_percentile"] - 0.0) < 0.001

    def test_ordering(self, node_details):
        assert node_details[0]["node_id"] == "service_api"
        assert node_details[-1]["node_id"] == "service_cache"


class TestStructure:
    """Report structural validation."""

    def test_report_has_sections(self, report):
        assert "summary" in report
        assert "incidents" in report
        assert "node_details" in report

    def test_summary_has_required_fields(self, summary):
        required = ["total_incidents", "nodes_affected", "max_severity",
                    "total_degraded_windows", "worst_node"]
        for field in required:
            assert field in summary

    def test_incident_has_required_fields(self, incidents):
        required = ["node_id", "start_window", "end_window",
                    "duration_windows", "peak_score", "severity"]
        for inc in incidents:
            for field in required:
                assert field in inc
