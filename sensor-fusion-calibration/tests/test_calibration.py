#!/usr/bin/env python3
"""
Integration tests for the sensor fusion calibration pipeline.

Tests validate the correctness of the final calibration output by checking:
- Aggregate confidence score statistics
- Calibration vector magnitudes
- Per-sensor calibration accuracy against reference values
- Consistency of precision rounding across positive and negative values
- Proper window coverage in calibration vector computation

These tests verify end-to-end pipeline behavior, not individual components.
"""

import json
import os
import subprocess
import sys
import math

# Paths
RUNTIME_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "environment", "runtime"
)
RUNTIME_DIR = os.path.normpath(RUNTIME_DIR)


def run_pipeline():
    """Execute the calibration pipeline and return parsed output."""
    result = subprocess.run(
        [sys.executable, "run_calibration.py"],
        capture_output=True,
        text=True,
        cwd=RUNTIME_DIR,
    )
    if result.returncode != 0:
        print(f"Pipeline execution failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    return json.loads(result.stdout)


def test_aggregate_confidence_bounds(data):
    """Verify aggregate confidence scores fall within expected bounds.

    The calibration pipeline should produce confidence scores that
    reflect sensor reliability across the network. Mean confidence
    should be within a tight tolerance of the expected value.
    """
    summary = data["summary"]
    avg_conf = summary["avg_confidence"]

    # Expected mean confidence for this dataset: ~0.2547
    expected_mean = 0.2547
    tolerance = 0.003

    if abs(avg_conf - expected_mean) > tolerance:
        return False, (
            f"Aggregate confidence out of bounds: "
            f"got {avg_conf:.6f}, expected {expected_mean:.4f} "
            f"(tolerance {tolerance})"
        )

    return True, "Aggregate confidence within bounds"


def test_calibration_magnitude_distribution(data):
    """Verify the distribution of calibration magnitudes is correct.

    Calibration magnitudes should reflect the proper combination of
    drift compensation, confidence weighting, and window averaging.
    The mean magnitude is sensitive to all pipeline stages.
    """
    records = data["calibration_records"]
    magnitudes = [r["magnitude"] for r in records]
    avg_mag = sum(magnitudes) / len(magnitudes)

    # Expected mean magnitude: ~0.0579
    expected_mean = 0.0579
    tolerance = 0.005

    if abs(avg_mag - expected_mean) > tolerance:
        return False, (
            f"Mean calibration magnitude incorrect: "
            f"got {avg_mag:.6f}, expected {expected_mean:.4f} "
            f"(tolerance {tolerance})"
        )

    # No sensor should have magnitude above 0.15 with correct pipeline
    max_mag = max(magnitudes)
    if max_mag > 0.13:
        return False, (
            f"Maximum magnitude too high: {max_mag:.4f} "
            f"(expected <= 0.13)"
        )

    return True, "Magnitude distribution correct"


def test_specific_sensor_calibration(data):
    """Verify specific sensor calibration vectors against reference.

    Checks a subset of sensors whose calibration vectors are known
    to be sensitive to pipeline correctness.
    """
    records = {r["sensor_id"]: r for r in data["calibration_records"]}

    # Reference values for key sensors
    reference = {
        "S001": {"confidence": 0.318, "magnitude": 0.065},
        "S010": {"confidence": 0.302, "magnitude": 0.113},
        "S020": {"confidence": 0.316, "magnitude": 0.082},
        "S030": {"confidence": 0.312, "magnitude": 0.062},
        "S040": {"confidence": 0.316, "magnitude": 0.064},
    }

    for sensor_id, ref in reference.items():
        if sensor_id not in records:
            return False, f"Missing sensor {sensor_id} in output"

        actual = records[sensor_id]

        # Check confidence within tolerance
        if abs(actual["confidence"] - ref["confidence"]) > 0.015:
            return False, (
                f"Sensor {sensor_id} confidence mismatch: "
                f"got {actual['confidence']}, expected {ref['confidence']}"
            )

        # Check magnitude within tolerance
        if abs(actual["magnitude"] - ref["magnitude"]) > 0.015:
            return False, (
                f"Sensor {sensor_id} magnitude mismatch: "
                f"got {actual['magnitude']}, expected {ref['magnitude']}"
            )

    return True, "Specific sensor calibrations correct"


def test_precision_rounding_consistency(data):
    """Verify that precision rounding is applied correctly for all values.

    Tests that negative values in calibration vectors are rounded correctly
    (toward nearest, not toward zero). Also verifies all values have
    at most 3 decimal places.
    """
    records = data["calibration_records"]

    for record in records:
        for value in record["calibration_vector"]:
            # Check decimal places
            rounded = round(value, 3)
            if abs(value - rounded) > 1e-10:
                return False, (
                    f"Sensor {record['sensor_id']} has value with "
                    f"excess precision: {value}"
                )

        # Verify confidence rounding
        conf_rounded = round(record["confidence"], 3)
        if abs(record["confidence"] - conf_rounded) > 1e-10:
            return False, (
                f"Sensor {record['sensor_id']} confidence not properly "
                f"rounded: {record['confidence']}"
            )

    # Specific check: verify a known negative value rounds correctly
    # S001 should have small negative values near zero, not large negatives
    s001 = next(r for r in records if r["sensor_id"] == "S001")
    neg_values = [v for v in s001["calibration_vector"] if v < 0]
    if neg_values:
        # With correct rounding, negative values should be small (close to 0)
        max_neg = min(neg_values)  # most negative
        if max_neg < -0.03:
            return False, (
                f"S001 has unexpectedly large negative value: {max_neg} "
                f"(suggests incorrect rounding for negative numbers)"
            )

    return True, "Precision rounding consistent"


def test_window_coverage_uniformity(data):
    """Verify calibration vectors show proper window coverage.

    With correct window boundaries, the calibration vector should show
    smooth transitions without edge artifacts. Tests that adjacent values
    in the vector don't show extreme discontinuities that would indicate
    undersized windows at boundaries.
    """
    records = data["calibration_records"]

    # Check a selection of sensors for vector smoothness
    test_sensors = ["S001", "S005", "S010", "S020", "S030"]

    for sensor_id in test_sensors:
        record = next((r for r in records if r["sensor_id"] == sensor_id), None)
        if record is None:
            continue

        vector = record["calibration_vector"]
        if len(vector) < 3:
            continue

        # Compute max step between adjacent values
        max_step = 0.0
        for i in range(1, len(vector)):
            step = abs(vector[i] - vector[i - 1])
            if step > max_step:
                max_step = step

        # With proper window coverage, max step should be bounded
        # Incorrect window sizes create artificial discontinuities
        if max_step > 0.08:
            return False, (
                f"Sensor {sensor_id} calibration vector has discontinuity: "
                f"max step = {max_step:.4f} (expected <= 0.08)"
            )

    return True, "Window coverage uniform"


def test_cross_cluster_consistency(data):
    """Verify that sensors in different clusters with shared references
    produce consistent calibration results.

    Sensors that share cross-references should have correlated confidence
    scores. Large discrepancies indicate scoring propagation errors.
    """
    records = {r["sensor_id"]: r for r in data["calibration_records"]}

    # Cross-referenced sensor pairs that should have correlated confidence
    # These pairs reference each other and should have similar confidence levels
    correlated_pairs = [
        ("S001", "S010"),  # alpha-beta thermal pair
        ("S007", "S016"),  # alpha-beta thermal pair
        ("S005", "S014"),  # alpha-beta vibration pair
    ]

    for s1, s2 in correlated_pairs:
        if s1 not in records or s2 not in records:
            continue

        conf_diff = abs(records[s1]["confidence"] - records[s2]["confidence"])
        # Confidence difference should be bounded for cross-referenced sensors
        if conf_diff > 0.025:
            return False, (
                f"Cross-cluster inconsistency between {s1} and {s2}: "
                f"confidence difference = {conf_diff:.4f} (expected <= 0.025)"
            )

    return True, "Cross-cluster consistency verified"


def main():
    """Run all calibration pipeline tests."""
    print("Running sensor fusion calibration tests...")
    print("=" * 60)

    data = run_pipeline()

    tests = [
        test_aggregate_confidence_bounds,
        test_calibration_magnitude_distribution,
        test_specific_sensor_calibration,
        test_precision_rounding_consistency,
        test_window_coverage_uniformity,
        test_cross_cluster_consistency,
    ]

    passed = 0
    failed = 0
    results = []

    for test_func in tests:
        test_name = test_func.__name__
        try:
            success, message = test_func(data)
            if success:
                print(f"  PASS: {test_name}")
                passed += 1
            else:
                print(f"  FAIL: {test_name}")
                print(f"        {message}")
                failed += 1
                results.append((test_name, message))
        except Exception as e:
            print(f"  ERROR: {test_name}")
            print(f"         {str(e)}")
            failed += 1
            results.append((test_name, str(e)))

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        print("\nFailed tests:")
        for name, msg in results:
            print(f"  - {name}: {msg}")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
