#!/usr/bin/env python3
"""Repair script for fleet telemetry monitor."""
import sys


def patch_analyzer():
    """Fix window step, speed spike comparison, and fuel accumulator."""
    path = "/app/runtime/analyzer.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug 1: off-by-one in step calculation
    content = content.replace(
        "self._step = self._window_size - self._overlap + 1",
        "self._step = self._window_size - self._overlap"
    )

    # Bug 2: speed spike uses >= but should use > (strict threshold)
    content = content.replace(
        "if r[\"speed\"] >= self._speed_threshold:",
        "if r[\"speed\"] > self._speed_threshold:"
    )

    # Bug 3: fuel drop accumulator resets instead of summing
    content = content.replace(
        "total_drop = delta",
        "total_drop += delta"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_scorer():
    """Fix weight accumulation in severity calculation."""
    path = "/app/runtime/scorer.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug 4: total_weight gets overwritten each iteration instead of accumulating
    content = content.replace(
        "total_weight = weight",
        "total_weight += weight"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_reporter():
    """Fix vehicle ordering to use numeric sort."""
    path = "/app/runtime/reporter.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug 5: lexicographic sort puts truck_12 before truck_2
    content = content.replace(
        "vehicle_order = sorted(grouped.keys())",
        "vehicle_order = sorted(grouped.keys(), key=lambda v: int(v.split('_')[1]))"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_analyzer()
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
