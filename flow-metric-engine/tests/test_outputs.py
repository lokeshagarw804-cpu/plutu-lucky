"""Validation tests for flow metric engine output."""
import hashlib
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
DATA_DIR = "/app/runtime/data"
REPORT_PATH = os.path.join(OUTPUT_DIR, "violation_report.json")
CLASS_PATH = os.path.join(OUTPUT_DIR, "classification_summary.json")


def load_report():
    """Load the violation report output."""
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


def load_classification():
    """Load the classification summary output."""
    with open(CLASS_PATH, "r") as f:
        return json.load(f)


def data_hash(filename):
    """SHA256 hash of a data file for integrity checking."""
    with open(os.path.join(DATA_DIR, filename), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_report_file_exists():
    """Violation report output must be generated."""
    assert os.path.isfile(REPORT_PATH)


def test_classification_file_exists():
    """Classification summary output must be generated."""
    assert os.path.isfile(CLASS_PATH)


def test_data_integrity_alpha():
    """Data file flow_alpha.json must not be tampered with."""
    assert data_hash("flow_alpha.json") == "97d92784523b1143b52020934f67e7cf60ae57809713a3243c99d379ba40e09c"


def test_data_integrity_delta():
    """Data file flow_delta.json must not be tampered with."""
    assert data_hash("flow_delta.json") == "c484a46eb64d1aaae1c2efe05e893c4d0e4b8f7b6f743cf142f0e62309b7b3e4"


def test_report_has_required_fields():
    """Report must contain threshold, total_flows, total_windows_analyzed, total_violations, flows."""
    report = load_report()
    for key in ("threshold", "total_flows", "total_windows_analyzed", "total_violations", "flows"):
        assert key in report, f"Missing field: {key}"


def test_total_flows():
    """Report must cover all 4 configured flows."""
    report = load_report()
    assert report["total_flows"] == 4


def test_total_windows_analyzed():
    """Total windows must equal 484 (121 per flow x 4 flows)."""
    report = load_report()
    assert report["total_windows_analyzed"] == 484, (
        f"Expected 484 total windows but got {report['total_windows_analyzed']}"
    )


def test_total_violations():
    """Total violations across all flows must be 152."""
    report = load_report()
    assert report["total_violations"] == 152, (
        f"Expected 152 violations but got {report['total_violations']}"
    )


def test_flow_delta_violations():
    """flow_delta must have exactly 105 violations."""
    report = load_report()
    delta = next((f for f in report["flows"] if f["flow_id"] == "flow_delta"), None)
    assert delta is not None, "flow_delta not found"
    assert delta["violations"] == 105, (
        f"flow_delta violations: expected 105, got {delta['violations']}"
    )


def test_flow_beta_violations():
    """flow_beta must have exactly 47 violations."""
    report = load_report()
    beta = next((f for f in report["flows"] if f["flow_id"] == "flow_beta"), None)
    assert beta is not None, "flow_beta not found"
    assert beta["violations"] == 47, (
        f"flow_beta violations: expected 47, got {beta['violations']}"
    )


def test_flow_alpha_no_violations():
    """flow_alpha must have zero violations."""
    report = load_report()
    alpha = next((f for f in report["flows"] if f["flow_id"] == "flow_alpha"), None)
    assert alpha is not None
    assert alpha["violations"] == 0


def test_flow_gamma_no_violations():
    """flow_gamma must have zero violations."""
    report = load_report()
    gamma = next((f for f in report["flows"] if f["flow_id"] == "flow_gamma"), None)
    assert gamma is not None
    assert gamma["violations"] == 0


def test_top_flow_is_delta():
    """Highest peak score must belong to flow_delta."""
    report = load_report()
    assert report["flows"][0]["flow_id"] == "flow_delta", (
        f"Expected top flow to be flow_delta, got {report['flows'][0]['flow_id']}"
    )


def test_flow_delta_violation_ratio():
    """flow_delta violation ratio must be between 0.85 and 0.90."""
    report = load_report()
    delta = next(f for f in report["flows"] if f["flow_id"] == "flow_delta")
    assert 0.85 < delta["violation_ratio"] < 0.90, (
        f"flow_delta ratio={delta['violation_ratio']}, expected 0.85-0.90"
    )


def test_flow_beta_violation_ratio():
    """flow_beta violation ratio must be between 0.35 and 0.42."""
    report = load_report()
    beta = next(f for f in report["flows"] if f["flow_id"] == "flow_beta")
    assert 0.35 < beta["violation_ratio"] < 0.42, (
        f"flow_beta ratio={beta['violation_ratio']}, expected 0.35-0.42"
    )


def test_classification_boundary_alpha():
    """flow_alpha must classify exactly 63 packets as small (boundary-sensitive)."""
    summary = load_classification()
    assert summary["flow_alpha"]["small"] == 63, (
        f"flow_alpha small count: expected 63, got {summary['flow_alpha']['small']}"
    )


def test_classification_boundary_gamma():
    """flow_gamma must have zero large packets (boundary-sensitive)."""
    summary = load_classification()
    assert summary["flow_gamma"]["large"] == 0, (
        f"flow_gamma large count: expected 0, got {summary['flow_gamma']['large']}"
    )
