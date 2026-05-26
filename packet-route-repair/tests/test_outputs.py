"""Tests for packet route analyzer output correctness."""
import json
import os

FLOWS_PATH = "/app/runtime/output/flows.json"
SUMMARY_PATH = "/app/runtime/output/summary.json"


def load_flows():
    with open(FLOWS_PATH, "r") as f:
        return json.load(f)


def load_summary():
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def test_flows_file_exists():
    """Output file flows.json must be created."""
    assert os.path.isfile(FLOWS_PATH), f"Missing: {FLOWS_PATH}"


def test_summary_file_exists():
    """Output file summary.json must be created."""
    assert os.path.isfile(SUMMARY_PATH), f"Missing: {SUMMARY_PATH}"



def test_flows_is_list():
    """flows.json must contain a JSON array."""
    flows = load_flows()
    assert isinstance(flows, list), "flows.json must be a list"


def test_flow_entry_fields():
    """Each flow must have required fields."""
    flows = load_flows()
    assert len(flows) > 0, "No flows generated"
    required = {"source_node", "dest_node", "anomaly_score", "path_cost",
                "optimal_cost", "has_loop"}
    for flow in flows:
        missing = required - set(flow.keys())
        assert not missing, f"Flow missing fields: {missing}"


def test_total_flows_count():
    """System must produce exactly 6 flow entries."""
    summary = load_summary()
    assert summary["total_flows"] == 6, (
        f"Expected 6 total flows but got {summary['total_flows']}"
    )


def test_loops_detected_count():
    """All 6 flows must have at least one loop detected."""
    summary = load_summary()
    assert summary["loops_detected"] == 6, (
        f"Expected 6 loops_detected but got {summary['loops_detected']}"
    )



def test_suboptimal_count():
    """All 6 flows must be flagged as suboptimal."""
    summary = load_summary()
    assert summary["suboptimal_count"] == 6, (
        f"Expected 6 suboptimal_count but got {summary['suboptimal_count']}"
    )


def test_max_anomaly_score():
    """Maximum anomaly score must be 1.0."""
    summary = load_summary()
    assert summary["max_anomaly_score"] == 1.0, (
        f"Expected max_anomaly_score=1.0 but got {summary['max_anomaly_score']}"
    )


def test_avg_anomaly_score():
    """Average anomaly score must be 0.7808."""
    summary = load_summary()
    assert abs(summary["avg_anomaly_score"] - 0.7808) < 0.001, (
        f"Expected avg_anomaly_score=0.7808 but got {summary['avg_anomaly_score']}"
    )



def test_first_flow_is_north_west():
    """Highest scoring flow must be north→west (score 1.0)."""
    flows = load_flows()
    assert flows[0]["source_node"] == "north", (
        f"First flow source should be 'north' but got '{flows[0]['source_node']}'"
    )
    assert flows[0]["dest_node"] == "west", (
        f"First flow dest should be 'west' but got '{flows[0]['dest_node']}'"
    )
    assert flows[0]["anomaly_score"] == 1.0


def test_west_east_flow_present():
    """west→east flow must be present with correct optimal cost."""
    flows = load_flows()
    we_flows = [f for f in flows if f["source_node"] == "west"
                and f["dest_node"] == "east"]
    assert len(we_flows) == 1, (
        f"Expected 1 west→east flow but got {len(we_flows)}"
    )
    assert we_flows[0]["optimal_cost"] == 20, (
        f"west→east optimal_cost should be 20 but got {we_flows[0]['optimal_cost']}"
    )



def test_east_west_optimal_cost():
    """east→west optimal cost must be 20 (via north: 8+12), not 22 (direct)."""
    flows = load_flows()
    ew_flows = [f for f in flows if f["source_node"] == "east"
                and f["dest_node"] == "west"]
    assert len(ew_flows) == 1, f"Expected 1 east→west flow, got {len(ew_flows)}"
    assert ew_flows[0]["optimal_cost"] == 20, (
        f"east→west optimal_cost should be 20 (via north) "
        f"but got {ew_flows[0]['optimal_cost']}"
    )


def test_east_west_anomaly_score():
    """east→west anomaly score must be 0.8198."""
    flows = load_flows()
    ew_flows = [f for f in flows if f["source_node"] == "east"
                and f["dest_node"] == "west"]
    assert len(ew_flows) == 1
    assert abs(ew_flows[0]["anomaly_score"] - 0.8198) < 0.001, (
        f"east→west anomaly_score should be 0.8198 "
        f"but got {ew_flows[0]['anomaly_score']}"
    )


def test_sort_order_descending_score():
    """Flows must be sorted by descending anomaly_score as primary key."""
    flows = load_flows()
    scores = [f["anomaly_score"] for f in flows]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], (
            f"Flow at index {i} (score={scores[i]}) should come before "
            f"index {i+1} (score={scores[i+1]})"
        )


def test_all_flows_have_loops():
    """Every flow in the output must have has_loop=True."""
    flows = load_flows()
    for flow in flows:
        assert flow["has_loop"] is True, (
            f"Flow {flow['source_node']}→{flow['dest_node']} "
            f"should have has_loop=True"
        )
