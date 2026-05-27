#!/usr/bin/env python3
"""Repair script for flow meter calibration pipeline."""
import sys


def patch_calibrator():
    """Fix polynomial evaluation order in calibrator."""
    path = "/app/runtime/calibrator.py"
    with open(path, "r") as f:
        content = f.read()

    # The bug: Horner's method iterates coefficients in storage order [a0,a1,a2,a3]
    # which computes ((a0*x + a1)*x + a2)*x + a3
    # Correct: iterate reversed so Horner gives a3*x^3 + a2*x^2 + a1*x + a0
    old = """        result = 0.0
        for coeff in self._coefficients:
            result = result * x + coeff
        return result"""

    new = """        result = 0.0
        for coeff in reversed(self._coefficients):
            result = result * x + coeff
        return result"""

    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)


def patch_compensator():
    """Fix temperature offset calculation in compensator."""
    path = "/app/runtime/compensator.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug: uses raw temperature instead of (temp - reference)
    old = "correction = 1.0 + self._factor * temp"
    new = "correction = 1.0 + self._factor * (temp - self._ref_temp)"

    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)


def patch_aggregator():
    """Fix interval boundary assignment in aggregator."""
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug: subtracts 1 from index for exact boundary timestamps
    # This incorrectly pushes boundary readings into prior interval
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
    """Fix compliance check to use compensated flow and numeric sort."""
    path = "/app/runtime/reporter.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug 1: string sort instead of numeric
    old = "meter_ids = sorted(aggregated_meters.keys())"
    new = "meter_ids = sorted(aggregated_meters.keys(), key=lambda s: int(s.split('_')[1]))"
    content = content.replace(old, new)

    # Bug 2: checks raw flow instead of compensated
    old = '                mean_flow = interval["mean_flow_raw"]'
    new = '                mean_flow = interval["mean_flow_compensated"]'
    content = content.replace(old, new)

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
