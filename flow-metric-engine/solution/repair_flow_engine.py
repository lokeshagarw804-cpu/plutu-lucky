#!/usr/bin/env python3
"""Repair script for flow metric engine."""
import sys


def patch_classifier():
    """Fix boundary comparison: use <= instead of < for upper bounds."""
    path = "/app/runtime/classifier.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        "if size < boundary:",
        "if size <= boundary:"
    )
    with open(path, "w") as f:
        f.write(content)


def patch_aggregator():
    """Fix window step: use configured step not window_size."""
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        "pos += self._window_size",
        "pos += self._window_step"
    )
    with open(path, "w") as f:
        f.write(content)


def patch_scorer():
    """Fix weight accumulation: += instead of =."""
    path = "/app/runtime/scorer.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        "total_weight = weight",
        "total_weight += weight"
    )
    with open(path, "w") as f:
        f.write(content)


def patch_reporter():
    """Fix violation ratio to use actual window count."""
    path = "/app/runtime/reporter.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        "expected_windows = 150 // self._window_size",
        "expected_windows = n_windows"
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_classifier()
    patch_aggregator()
    patch_scorer()
    patch_reporter()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.main import main as run_main
    run_main()


if __name__ == "__main__":
    main()
