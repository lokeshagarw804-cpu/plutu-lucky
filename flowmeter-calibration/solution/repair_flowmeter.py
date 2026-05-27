#!/usr/bin/env python3
"""Repair script for flow meter calibration pipeline."""
import sys


def patch_calibrator():
    """Fix polynomial evaluation in calibrator.

    Two issues:
    1. Horner's method iterates coefficients in storage order [a0,a1,a2,a3]
       but Horner's requires highest-degree first, so must use reversed().
    2. Voltage is incorrectly normalized by reference_voltage before evaluation.
       The polynomial coefficients are calibrated for raw voltage input.
    """
    path = "/app/runtime/calibrator.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix 1: Remove spurious voltage normalization
    content = content.replace(
        "                # Normalize voltage against reference for calibration stability\n"
        "                normalized_v = voltage / self._ref_voltage\n"
        "                flow = self._evaluate_polynomial(normalized_v)",
        "                flow = self._evaluate_polynomial(voltage)"
    )

    # Fix 2: Reverse coefficient iteration for correct Horner's evaluation
    content = content.replace(
        "        for coeff in self._coefficients:",
        "        for coeff in reversed(self._coefficients):"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_compensator():
    """Fix temperature offset calculation in compensator.

    Uses absolute temperature instead of offset from reference.
    Should be: (temp - ref_temp) not just temp.
    """
    path = "/app/runtime/compensator.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "correction = 1.0 + self._factor * temp",
        "correction = 1.0 + self._factor * (temp - self._ref_temp)"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_aggregator():
    """Fix interval boundary assignment in aggregator.

    Boundary timestamps are incorrectly assigned to the prior interval.
    Timestamp 60 should be in interval 1, not interval 0.
    """
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()

    old = """        idx = timestamp // self._interval_sec
        if timestamp > 0 and timestamp % self._interval_sec == 0:
            idx -= 1
        return idx"""

    new = """        idx = timestamp // self._interval_sec
        return idx"""

    content = content.replace(old, new)

    with open(path, "w") as f:
        f.write(content)


def patch_reporter():
    """Fix compliance check and meter ordering in reporter.

    1. Sorts meter IDs lexicographically instead of by numeric suffix.
    2. Checks mean_flow_raw instead of mean_flow_compensated for limits.
    """
    path = "/app/runtime/reporter.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix sort order
    content = content.replace(
        "meter_ids = sorted(aggregated_meters.keys())",
        "meter_ids = sorted(aggregated_meters.keys(), key=lambda s: int(s.split('_')[1]))"
    )

    # Fix compliance check to use compensated flow
    content = content.replace(
        'mean_flow = interval["mean_flow_raw"]',
        'mean_flow = interval["mean_flow_compensated"]'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_calibrator()
    patch_compensator()
    patch_aggregator()
    patch_reporter()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.main import main as run_main
    run_main()


if __name__ == "__main__":
    main()
