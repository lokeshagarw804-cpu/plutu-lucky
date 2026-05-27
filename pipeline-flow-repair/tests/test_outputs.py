"""Validation tests for pipeline flow monitoring system output."""
import hashlib
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
DATA_DIR = "/app/runtime/data"
REPORT_PATH = os.path.join(OUTPUT_DIR, "pipeline_report.json")
FLOW_PATH = os.path.join(OUTPUT_DIR, "flow_summary.json")


def load_report():
    """Load pipeline report JSON."""
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


def load_flow_summary():
    """Load flow summary JSON."""
    with open(FLOW_PATH, "r") as f:
        return json.load(f)


def test_report_file_exists():
    """Pipeline report output file must be generated at the expected path."""
    assert os.path.isfile(REPORT_PATH)


def test_flow_summary_file_exists():
    """Flow summary output file must be generated at the expected path."""
    assert os.path.isfile(FLOW_PATH)


def test_report_has_required_fields():
    """Report must contain all required top-level fields."""
    report = load_report()
    required = ["segment_order", "total_segments", "total_pressure_anomalies",
                "total_leaks", "total_blockages", "max_severity", "segments"]
    for field in required:
        assert field in report, f"Missing field: {field}"


def test_flow_summary_has_required_fields():
    """Flow summary must contain segment_order, segments, and total_volume."""
    summary = load_flow_summary()
    assert "segment_order" in summary
    assert "segments" in summary
    assert "total_volume" in summary


def test_segment_order():
    """Segments must be ordered by configured upstream topology, not alphabetically."""
    report = load_report()
    expected_order = ["seg_1", "seg_2", "seg_3", "seg_10", "seg_11"]
    assert report["segment_order"] == expected_order, (
        f"Expected order {expected_order} but got {report['segment_order']}"
    )


def test_total_segments():
    """Report must include all 5 active pipeline segments."""
    report = load_report()
    assert report["total_segments"] == 5


def test_total_pressure_anomalies():
    """System must detect exactly 19 pressure anomaly events across all segments."""
    report = load_report()
    assert report["total_pressure_anomalies"] == 19, (
        f"Expected 19 anomalies but got {report['total_pressure_anomalies']}"
    )


def test_total_leaks():
    """Exactly 7 anomalies must be classified as leaks."""
    report = load_report()
    assert report["total_leaks"] == 7, (
        f"Expected 7 leaks but got {report['total_leaks']}"
    )


def test_total_blockages():
    """Exactly 12 anomalies must be classified as blockages."""
    report = load_report()
    assert report["total_blockages"] == 12, (
        f"Expected 12 blockages but got {report['total_blockages']}"
    )


def test_max_severity_bounded():
    """Maximum severity must be between 0 and 1 exclusive of 1.0."""
    report = load_report()
    assert 0 < report["max_severity"] < 1.0, (
        f"max_severity={report['max_severity']} should be in (0, 1.0)"
    )


def test_max_severity_value():
    """Maximum severity across all anomalies must be approximately 0.5125."""
    report = load_report()
    assert abs(report["max_severity"] - 0.5125) < 0.01, (
        f"Expected max_severity≈0.5125 but got {report['max_severity']}"
    )


def test_total_flow_volume():
    """Total cumulative flow volume must be approximately 0.0299 m³."""
    summary = load_flow_summary()
    assert abs(summary["total_volume"] - 0.0299) < 0.001, (
        f"Expected total_volume≈0.0299 but got {summary['total_volume']}"
    )


def test_seg_2_has_one_anomaly():
    """Segment seg_2 must have exactly 1 pressure anomaly (boundary case)."""
    report = load_report()
    seg_2 = [s for s in report["segments"] if s["segment_id"] == "seg_2"]
    assert len(seg_2) == 1
    assert seg_2[0]["pressure_anomaly_count"] == 1, (
        f"seg_2 should have 1 anomaly but has {seg_2[0]['pressure_anomaly_count']}"
    )


def test_seg_3_classification_is_leak():
    """All anomalies in seg_3 must be classified as leaks (not blockages)."""
    report = load_report()
    seg_3 = [s for s in report["segments"] if s["segment_id"] == "seg_3"]
    assert len(seg_3) == 1
    for entry in seg_3[0]["classifications"]:
        assert entry["classification"] == "leak", (
            f"seg_3 anomaly at index {entry['reading_index']} should be leak "
            f"but got {entry['classification']}"
        )


def test_seg_10_classification_is_blockage():
    """All anomalies in seg_10 must be classified as blockages."""
    report = load_report()
    seg_10 = [s for s in report["segments"] if s["segment_id"] == "seg_10"]
    assert len(seg_10) == 1
    for entry in seg_10[0]["classifications"]:
        assert entry["classification"] == "blockage", (
            f"seg_10 anomaly at index {entry['reading_index']} should be blockage "
            f"but got {entry['classification']}"
        )


def test_seg_3_severity_uniform():
    """All seg_3 anomalies must have identical severity of 0.3625."""
    report = load_report()
    seg_3 = [s for s in report["segments"] if s["segment_id"] == "seg_3"]
    assert len(seg_3) == 1
    for entry in seg_3[0]["classifications"]:
        assert abs(entry["severity"] - 0.3625) < 0.005, (
            f"seg_3 severity should be 0.3625 but got {entry['severity']}"
        )


def test_data_files_integrity():
    """Input data files must not be modified from their original state."""
    expected_hashes = {
        'seg_1.json': 'f85798783e68966a4a48d281770f3b7bd94c8a80b09e24312e114c21f6d023b6',
        'seg_10.json': 'a681d019739d20ab7a64d855f1428e42b489625c1e02b2e602da5529e455c93d',
        'seg_11.json': '478cab88be63dd1dc6356c539e302759436996263c437401a3237fcfc18e885d',
        'seg_2.json': '1bc1388c57f3d52954e372d62d805d6abdc1ff15a4228e0866ef3ca483915a94',
        'seg_3.json': 'db15f1e1145d61206b468722f6619598c04cc9b6cc3e96ed913c27c442fe3f59',
    }
    for fname, expected_hash in expected_hashes.items():
        fpath = os.path.join(DATA_DIR, fname)
        assert os.path.isfile(fpath), f"Data file missing: {fname}"
        with open(fpath, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        assert actual_hash == expected_hash, (
            f"Data file {fname} has been modified (hash mismatch)"
        )
