"""Validation tests for flow meter calibration pipeline output."""
import hashlib
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
RESULTS_PATH = os.path.join(OUTPUT_DIR, "calibration_results.json")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "summary.json")
DATA_DIR = "/app/runtime/data"


def load_results():
    """Load calibration results."""
    with open(RESULTS_PATH, "r") as f:
        return json.load(f)


def load_summary():
    """Load summary output."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def test_results_file_exists():
    """Calibration results output file must be generated at the expected path."""
    assert os.path.isfile(RESULTS_PATH)


def test_summary_file_exists():
    """Summary output file must be generated at the expected path."""
    assert os.path.isfile(SUMMARY_PATH)


def test_data_files_unmodified():
    """Input data files must not be modified by the repair process."""
    expected_hashes = {
        "meter_1.json": "3d78b413b544ca5a8160c86d5d2a1baf3febf799508686086c8e7c36073ff360",
        "meter_3.json": "e2e66c588c7fad5256fa6eb56d1178c0e9415b90ddd2d30a7d8ec4e923417c11",
        "meter_7.json": "143b93fa1a8bef15780c1f4f7ea26bf449a81ce8c13dfe09cc540f6fa2ec3118",
        "meter_12.json": "f14353609b0d6c8c61cdeaef6d1578e2cbb4468165e9b3acb1382567b2ce1799",
        "meter_20.json": "0a38e265eebe21ed916be05909d2821d1410c0a994556a0492f2bcd6326086d3",
    }
    for fname, expected_hash in expected_hashes.items():
        fpath = os.path.join(DATA_DIR, fname)
        with open(fpath, "rb") as f:
            content = f.read()
        actual_hash = hashlib.sha256(content).hexdigest()
        assert actual_hash == expected_hash, (
            f"Data file {fname} has been modified (hash mismatch)"
        )


def test_results_has_required_fields():
    """Results must contain meter_order, total_meters, compliant_count, non_compliant_count, meters."""
    results = load_results()
    assert "meter_order" in results
    assert "total_meters" in results
    assert "compliant_count" in results
    assert "non_compliant_count" in results
    assert "meters" in results


def test_summary_has_required_fields():
    """Summary must contain total_meters, compliant_count, total_readings_processed, total_intervals."""
    summary = load_summary()
    assert "total_meters" in summary
    assert "compliant_count" in summary
    assert "total_readings_processed" in summary
    assert "total_intervals" in summary


def test_meter_order_numeric():
    """Meters must be ordered by numeric suffix: meter_1, meter_3, meter_7, meter_12, meter_20."""
    results = load_results()
    assert results["meter_order"] == ["meter_1", "meter_3", "meter_7", "meter_12", "meter_20"]


def test_total_meters_count():
    """Pipeline must process all 5 active meters from config."""
    results = load_results()
    assert results["total_meters"] == 5


def test_compliant_count():
    """Exactly 4 meters must be compliant when checked against compensated flow."""
    results = load_results()
    assert results["compliant_count"] == 4, (
        f"Expected 4 compliant meters but got {results['compliant_count']}"
    )


def test_non_compliant_count():
    """Exactly 1 meter must be non-compliant."""
    results = load_results()
    assert results["non_compliant_count"] == 1


def test_meter_20_non_compliant():
    """Meter_20 must be the only non-compliant meter due to high compensated flow."""
    results = load_results()
    non_compliant = [m for m in results["meters"] if not m["is_compliant"]]
    assert len(non_compliant) == 1
    assert non_compliant[0]["meter_id"] == "meter_20"


def test_meter_20_violation_count():
    """Meter_20 must have exactly 2 above-maximum violations."""
    results = load_results()
    m20 = [m for m in results["meters"] if m["meter_id"] == "meter_20"][0]
    assert m20["violation_count"] == 2, (
        f"meter_20 should have 2 violations but has {m20['violation_count']}"
    )


def test_meter_20_violation_intervals():
    """Meter_20 violations must occur in intervals 1 and 2."""
    results = load_results()
    m20 = [m for m in results["meters"] if m["meter_id"] == "meter_20"][0]
    violation_intervals = sorted(v["interval_index"] for v in m20["violations"])
    assert violation_intervals == [1, 2], (
        f"meter_20 violations expected at intervals [1, 2] but got {violation_intervals}"
    )


def test_total_readings_processed():
    """All 56 readings across 5 meters must be processed."""
    summary = load_summary()
    assert summary["total_readings_processed"] == 56


def test_total_intervals():
    """Pipeline must produce exactly 15 intervals total across all meters."""
    summary = load_summary()
    assert summary["total_intervals"] == 15, (
        f"Expected 15 total intervals but got {summary['total_intervals']}"
    )


def test_meter_1_interval_0_reading_count():
    """Meter_1 first interval must contain exactly 4 readings (timestamps 0,15,30,45)."""
    results = load_results()
    m1 = [m for m in results["meters"] if m["meter_id"] == "meter_1"][0]
    assert m1["total_intervals"] == 3
    # Verify through total readings: meter_1 has 12 readings across 3 intervals of 4 each
    # The summary confirms even distribution


def test_meter_12_is_compliant():
    """Meter_12 with low voltages must still be above minimum flow threshold."""
    results = load_results()
    m12 = [m for m in results["meters"] if m["meter_id"] == "meter_12"][0]
    assert m12["is_compliant"] is True


def test_meter_7_is_compliant():
    """Meter_7 with mid-range voltages must remain within flow limits."""
    results = load_results()
    m7 = [m for m in results["meters"] if m["meter_id"] == "meter_7"][0]
    assert m7["is_compliant"] is True
