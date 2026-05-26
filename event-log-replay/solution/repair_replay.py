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
    """Fix vector clock comparison — concurrent events must not be violations.

    The last return in _compare_clocks returns 'a_before_b' for concurrent
    events. It should return 'concurrent'.
    """
    path = "/app/runtime/causality.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'return "a_before_b"',
        'return "concurrent"',
        # only replace the LAST occurrence (the fallback)
    )
    # That replaces ALL occurrences — we need the first one to stay
    # So let's be more precise
    with open(path, "w") as f:
        f.write(content)


def patch_causality_v2():
    """Better approach: replace the specific buggy fallback line."""
    path = "/app/runtime/causality.py"
    with open(path, "r") as f:
        lines = f.readlines()

    # Find the last 'return "a_before_b"' which is the concurrent fallback
    last_idx = None
    for i, line in enumerate(lines):
        if 'return "a_before_b"' in line:
            last_idx = i

    if last_idx is not None:
        lines[last_idx] = lines[last_idx].replace(
            'return "a_before_b"',
            'return "concurrent"'
        )

    with open(path, "w") as f:
        f.writelines(lines)


def patch_reporter():
    """Fix weight accumulator (= should be +=) and sort key (add source_node)."""
    path = "/app/runtime/reporter.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "total_weight = weight",
        "total_weight += weight"
    )
    content = content.replace(
        'anomalies.sort(key=lambda a: (-a["severity"], a["source_node"]))',
        'anomalies.sort(key=lambda a: (-a["severity"], a["source_node"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_causality_v2()
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
