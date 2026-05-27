"""
Tests for the telemetry batch reconciler output.
Validates /output/reconciliation_report.json against expected behavior.
"""
import hashlib
import json
import os
import pytest


REPORT_PATH = "/output/reconciliation_report.json"
DATA_DIR = "/environment/runtime/data"


@pytest.fixture
def report():
    """Load the reconciliation report."""
    assert os.path.exists(REPORT_PATH), "Report not found at /output/reconciliation_report.json"
    with open(REPORT_PATH) as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def verify_data_integrity():
    """Verify data files have not been tampered with."""
    checksums = {
        "batches.json": "92f13d49cae3ee1d35f814a142aa6d48cb074f4ab52f4a87d6f6de6516d3338f",
        "retry_log.json": "5fae0f3faaa7f0d1bd814481ca712799396025cb65a3212ce78ce41422e1540d",
        "settlements.json": "9661ddb0526e895c67761d64ce7867981ca75edc59ea281f0ae70d41a10f5d82",
    }
    for fname, expected_hash in checksums.items():
        fpath = os.path.join(DATA_DIR, fname)
        with open(fpath, "rb") as f:
            actual = hashlib.sha256(f.read()).hexdigest()
        assert actual == expected_hash, f"Data file {fname} has been modified"


def test_report_structure(report):
    """Report must contain all required top-level keys with correct counts."""
    assert "batch_summaries" in report
    assert "station_totals" in report
    assert "state_report" in report
    assert len(report["batch_summaries"]) == 6
    assert len(report["station_totals"]) == 3
    assert len(report["state_report"]) == 6
    # All state reports must show a terminal state
    terminal_states = {"SETTLED", "FAILED"}
    for sr in report["state_report"]:
        assert sr["final_state"] in terminal_states, (
            f"Batch {sr['batch_id']} in non-terminal state: {sr['final_state']}"
        )


def test_total_event_count_alpha(report):
    """Alpha station must have exactly 9 events with correct per-batch split."""
    alpha = next(s for s in report["station_totals"] if s["station"] == "alpha")
    assert alpha["total_events"] == 9
    # Verify the split: B001 must have 5, B002 must have 4
    b001 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B001")
    b002 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B002")
    assert b001["event_count"] + b002["event_count"] == 9
    assert b001["event_count"] > b002["event_count"]


def test_total_event_count_beta(report):
    """Beta station must have exactly 8 events after boundary dedup."""
    beta = next(s for s in report["station_totals"] if s["station"] == "beta")
    assert beta["total_events"] == 8


def test_total_event_count_gamma(report):
    """Gamma station must have exactly 9 events with correct boundary handling."""
    gamma = next(s for s in report["station_totals"] if s["station"] == "gamma")
    assert gamma["total_events"] == 9
    # B005 keeps boundary, B006 excludes it
    b005 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B005")
    b006 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B006")
    assert b005["event_count"] == 5
    assert b006["event_count"] == 4


def test_batch_b001_event_count(report):
    """B001 includes boundary event at ts=1004 (belongs to earlier batch)."""
    b001 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B001")
    assert b001["event_count"] == 5


def test_batch_b002_event_count(report):
    """B002 excludes boundary at ts=1004 (belongs to B001)."""
    b002 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B002")
    assert b002["event_count"] == 4


def test_batch_b003_event_count(report):
    """B003 includes all events including boundary at ts=1003."""
    b003 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B003")
    assert b003["event_count"] == 5


def test_batch_b004_boundary_dedup(report):
    """B004 excludes boundary events at ts=1003 (belong to B003)."""
    b004 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B004")
    assert b004["event_count"] == 3
    # Verify the excluded events are not present
    ts_values = [e["ts"] for e in b004["sorted_events"]]
    assert 1003 not in ts_values


def test_batch_b001_mean_precision(report):
    """B001 mean must be computed as sum/count (not incremental) to 4 decimals."""
    b001 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B001")
    # Expected: (12.5 + 14.2 + 11.8 + 13.1 + 15.0) / 5 = 66.6 / 5 = 13.32
    assert b001["mean_value"] == 13.32


def test_batch_b002_mean_value(report):
    """B002 mean after boundary exclusion."""
    b002 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B002")
    # Events: 17.1, 12.9, 14.4, 13.7 -> sum=58.1, mean=14.525
    assert b002["mean_value"] == 14.525


def test_batch_b004_mean_value(report):
    """B004 mean after boundary exclusion (only 3 events)."""
    b004 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B004")
    # Events at ts>1003: ts=1004 val=23.6, ts=1005 val=21.3, ts=1006 val=24.7
    # sum=69.6, mean=23.2
    assert b004["mean_value"] == 23.2


def test_deterministic_sort_b003(report):
    """B003 has events with same ts=1001 - must be sorted by (ts, seq)."""
    b003 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B003")
    events = b003["sorted_events"]
    # Events at ts=1001: seq=2 (val=23.4) must come before seq=3 (val=21.7)
    ts1001_events = [e for e in events if e["ts"] == 1001]
    assert len(ts1001_events) == 2
    assert ts1001_events[0]["seq"] == 2
    assert ts1001_events[1]["seq"] == 3


def test_deterministic_sort_b005(report):
    """B005 has events with same ts=1002 - must be sorted by (ts, seq)."""
    b005 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B005")
    events = b005["sorted_events"]
    ts1002_events = [e for e in events if e["ts"] == 1002]
    assert len(ts1002_events) == 2
    assert ts1002_events[0]["seq"] == 3
    assert ts1002_events[1]["seq"] == 4


def test_deterministic_sort_b006(report):
    """B006 has events with same ts=1006 - after dedup must have correct sort."""
    b006 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B006")
    events = b006["sorted_events"]
    ts1006_events = [e for e in events if e["ts"] == 1006]
    assert len(ts1006_events) == 2
    assert ts1006_events[0]["seq"] == 9
    assert ts1006_events[1]["seq"] == 10


def test_all_batches_settled(report):
    """All batches must reach SETTLED as final state."""
    for sr in report["state_report"]:
        assert sr["final_state"] == "SETTLED", (
            f"Batch {sr['batch_id']} has final_state={sr['final_state']}, expected SETTLED"
        )


def test_b004_settled_terminal(report):
    """B004 must be SETTLED - the RETRY settlement action must be rejected."""
    b004 = next(s for s in report["state_report"] if s["batch_id"] == "B004")
    assert b004["final_state"] == "SETTLED"
    # B004 has settlement RETRY after SETTLE - must be rejected
    # History: PENDING->PROCESSING->FAILED->RETRYING->PROCESSING->...->SETTLED
    # The RETRY action at ts=1400 must NOT change state
    assert b004["retry_count"] == 3


def test_b002_retry_count(report):
    """B002 had 2 failures before success - retry count should be 2."""
    b002 = next(s for s in report["state_report"] if s["batch_id"] == "B002")
    assert b002["retry_count"] == 2


def test_b006_retry_count(report):
    """B006 had 1 failure before success - retry count should be 1."""
    b006 = next(s for s in report["state_report"] if s["batch_id"] == "B006")
    assert b006["retry_count"] == 1
    assert b006["final_state"] == "SETTLED"
    # PENDING, PROCESSING, FAILED, RETRYING, PROCESSING, SETTLED = 6
    assert b006["history_length"] == 6
    # B006 should have 4 events after dedup (excludes boundary at ts=1003)
    b006_summary = next(s for s in report["batch_summaries"] if s["batch_id"] == "B006")
    assert b006_summary["event_count"] == 4


def test_b004_history_length(report):
    """B004 history must reflect 3 retry cycles plus settlement."""
    b004 = next(s for s in report["state_report"] if s["batch_id"] == "B004")
    # PENDING, PROCESSING, FAILED, RETRYING, PROCESSING, FAILED, RETRYING,
    # PROCESSING, FAILED, RETRYING, PROCESSING, SETTLED = 12
    assert b004["history_length"] == 12


def test_station_totals_overall_mean_alpha(report):
    """Alpha overall mean must be weighted correctly across batches."""
    alpha = next(s for s in report["station_totals"] if s["station"] == "alpha")
    # B001: 5 events, mean=13.32 -> sum=66.6
    # B002: 4 events, mean=14.525 -> sum=58.1
    # Total: 9 events, sum=124.7, mean=124.7/9=13.8556
    assert alpha["overall_mean"] == 13.8556


def test_station_totals_overall_mean_beta(report):
    """Beta overall mean reflects the 3-event B004 after boundary dedup."""
    beta = next(s for s in report["station_totals"] if s["station"] == "beta")
    # B003: 5 events, mean=22.8 -> sum=114.0
    # B004: 3 events, mean=23.2 -> sum=69.6
    # Total: 8 events, sum=183.6, mean=183.6/8=22.95
    assert beta["overall_mean"] == 22.95


def test_station_totals_sorted_alphabetically(report):
    """Station totals must be sorted alphabetically with correct batch_ids."""
    stations = [s["station"] for s in report["station_totals"]]
    assert stations == sorted(stations)
    assert stations == ["alpha", "beta", "gamma"]
    # Verify batch_ids are present in correct order
    alpha = report["station_totals"][0]
    assert "B001" in alpha["batch_ids"]
    assert "B002" in alpha["batch_ids"]
    # Beta must have exactly 8 events (not 9)
    beta = report["station_totals"][1]
    assert beta["total_events"] == 8


def test_batch_summaries_min_max_b004(report):
    """B004 min/max must reflect only non-boundary events."""
    b004 = next(s for s in report["batch_summaries"] if s["batch_id"] == "B004")
    # Only events at ts>1003: values are 23.6, 21.3, 24.7
    assert b004["min_value"] == 21.3
    assert b004["max_value"] == 24.7
