#!/usr/bin/env python3
"""Patches bugs in the event log replay engine and re-runs it."""
import subprocess
import sys


def patch_loader():
    """Fix merge window boundary: < should be <="""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        "if event[\"ts_ms\"] - group_start < self._window_ms:",
        "if event[\"ts_ms\"] - group_start <= self._window_ms:"
    )
    with open(path, "w") as f:
        f.write(content)


def patch_causality():
    """Fix vector clock comparison.

    Three issues:
    1. When a_dominates, A happened AFTER B, so B is before A -> "b_before_a"
       But code returns "a_before_b" (swapped)
    2. When b_dominates, B happened AFTER A, so A is before B -> "a_before_b"
       But code returns "b_before_a" (swapped)
    3. Concurrent fallback returns "a_before_b" instead of "concurrent"
    """
    path = "/app/runtime/causality.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix the swapped labels and concurrent fallback
    old_block = (
        '        if a_dominates and a_has_greater:\n'
        '            return "a_before_b"\n'
        '        if b_dominates and b_has_greater:\n'
        '            return "b_before_a"\n'
        '\n'
        '        # Both have some greater values — should be concurrent\n'
        '        # but we check if clocks are actually equal\n'
        '        if not a_has_greater and not b_has_greater:\n'
        '            return "concurrent"\n'
        '\n'
        '        return "a_before_b"'
    )
    new_block = (
        '        if a_dominates and a_has_greater:\n'
        '            return "b_before_a"\n'
        '        if b_dominates and b_has_greater:\n'
        '            return "a_before_b"\n'
        '\n'
        '        return "concurrent"'
    )
    content = content.replace(old_block, new_block)

    with open(path, "w") as f:
        f.write(content)


def patch_reporter():
    """Fix weight accumulator: = should be +="""
    path = "/app/runtime/reporter.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        "total_weight = weight",
        "total_weight += weight"
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_causality()
    patch_reporter()

    # Re-run with fixes
    result = subprocess.run(
        ["python3", "-m", "runtime.main"],
        cwd="/app",
        capture_output=True
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
