#!/usr/bin/env python3
"""
Repair script for the sensor fusion calibration pipeline.

Fixes the following issues in the runtime:
1. confidence_scorer.py: Cache accumulation bug where _confidence_cache
   accumulates values across evaluations instead of storing final values.
2. drift_compensator.py: Pass count scaling bug where _pass_count multiplier
   causes progressive drift over-correction for later clusters.
3. matrix_assembler.py: Window slice boundary bug where exclusive end index
   produces undersized windows at array boundaries.
4. calibrator.py: Truncation rounding bug where int() truncation toward zero
   produces incorrect results for negative values.
"""

import os
import re


def fix_confidence_scorer(runtime_dir):
    """Fix the cache accumulation bug in confidence_scorer.py.

    The bug: self._neighbor_score_cache[neighbor_id] accumulates values across
    multiple evaluations instead of storing the computed value directly.
    This causes inflated propagation scores for sensors that appear as
    cross-reference targets from multiple source sensors.
    """
    filepath = os.path.join(runtime_dir, "confidence_scorer.py")
    with open(filepath, "r") as f:
        content = f.read()

    # Replace the accumulating cache assignment with direct assignment
    old = (
        "self._neighbor_score_cache[neighbor_id] = (\n"
        "            self._neighbor_score_cache.get(neighbor_id, 0.0) + propagation_value\n"
        "        )"
    )
    new = "self._neighbor_score_cache[neighbor_id] = propagation_value"

    content = content.replace(old, new)

    with open(filepath, "w") as f:
        f.write(content)

    print("Fixed: confidence_scorer.py - cache accumulation bug")


def fix_drift_compensator(runtime_dir):
    """Fix the pass count scaling bug in drift_compensator.py.

    The bug: drift_magnitude uses self._pass_count as a multiplier, but
    _pass_count increments once per cluster call. This means later clusters
    get progressively larger drift corrections (2x, 3x, 4x, 5x) instead
    of uniform correction.
    """
    filepath = os.path.join(runtime_dir, "drift_compensator.py")
    with open(filepath, "r") as f:
        content = f.read()

    # Remove the pass_count multiplier from the drift formula
    old = "drift_magnitude = drift_rate * self._pass_count * (1.0 - math.exp(-t / tau))"
    new = "drift_magnitude = drift_rate * (1.0 - math.exp(-t / tau))"

    content = content.replace(old, new)

    with open(filepath, "w") as f:
        f.write(content)

    print("Fixed: drift_compensator.py - pass count scaling bug")


def fix_matrix_assembler(runtime_dir):
    """Fix the window slice boundary bug in matrix_assembler.py.

    The bug: end = min(n, start + window) uses exclusive boundary which
    produces windows smaller than intended at the array edges. Should be
    start + window + 1 for proper inclusive coverage.
    """
    filepath = os.path.join(runtime_dir, "matrix_assembler.py")
    with open(filepath, "r") as f:
        content = f.read()

    old = "end = min(n, start + window)"
    new = "end = min(n, start + window + 1)"

    content = content.replace(old, new)

    with open(filepath, "w") as f:
        f.write(content)

    print("Fixed: matrix_assembler.py - window slice boundary bug")


def fix_calibrator(runtime_dir):
    """Fix the truncation rounding bug in calibrator.py.

    The bug: int(value * factor) / factor truncates toward zero, which gives
    incorrect results for negative numbers. Should use round() for proper
    nearest-value rounding.
    """
    filepath = os.path.join(runtime_dir, "calibrator.py")
    with open(filepath, "r") as f:
        content = f.read()

    old = "        factor = 10 ** self._decimal_places\n        return int(value * factor) / factor"
    new = "        return round(value, self._decimal_places)"

    content = content.replace(old, new)

    with open(filepath, "w") as f:
        f.write(content)

    print("Fixed: calibrator.py - truncation rounding bug")


def main():
    """Apply all fixes to the runtime directory."""
    runtime_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "environment", "runtime"
    )
    runtime_dir = os.path.normpath(runtime_dir)

    if not os.path.isdir(runtime_dir):
        print(f"Error: Runtime directory not found: {runtime_dir}")
        return 1

    fix_confidence_scorer(runtime_dir)
    fix_drift_compensator(runtime_dir)
    fix_matrix_assembler(runtime_dir)
    fix_calibrator(runtime_dir)

    print("\nAll fixes applied successfully.")
    return 0


if __name__ == "__main__":
    exit(main())
