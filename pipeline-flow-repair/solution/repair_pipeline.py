#!/usr/bin/env python3
"""Repair script for pipeline flow monitoring system."""
import sys


def patch_flow_aggregator():
    """Fix accumulator reset bug in trapezoidal integration."""
    path = "/app/runtime/flow_aggregator.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "                total_volume = avg_segment_flow * dt",
        "                total_volume += avg_segment_flow * dt"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_anomaly_detector():
    """Fix consecutive count comparison from > to >=."""
    path = "/app/runtime/anomaly_detector.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "                    if consecutive_count > self._min_consecutive:",
        "                    if consecutive_count >= self._min_consecutive:"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_segment_sorter():
    """Fix sorting to use configured reference order instead of alphabetical."""
    path = "/app/runtime/segment_sorter.py"
    with open(path, "r") as f:
        content = f.read()

    # The sort_segments method filters by reference order then re-sorts alphabetically
    # It should just return the filtered reference order without the final sort
    old = """        available = [s for s in self._reference_order if s in segments]
        # Ensure any segments not in reference are still included
        extras = sorted(k for k in segments if k not in available)
        return sorted(available + extras)"""

    new = """        available = [s for s in self._reference_order if s in segments]
        # Ensure any segments not in reference are still included
        extras = sorted(k for k in segments if k not in available)
        return available + extras"""

    content = content.replace(old, new)

    with open(path, "w") as f:
        f.write(content)


def patch_leak_classifier():
    """Fix two bugs: missing length division and accumulator reset in severity."""
    path = "/app/runtime/leak_classifier.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug 5: divide by segment length for per-unit-length rate
    content = content.replace(
        "                drop_rate = abs(anomaly[\"actual\"] - anomaly[\"expected\"])",
        "                drop_rate = abs(anomaly[\"actual\"] - anomaly[\"expected\"]) / length"
    )

    # Fix Bug 2: accumulator reset in severity calculation
    content = content.replace(
        "            total_weight = weight",
        "            total_weight += weight"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_flow_aggregator()
    patch_anomaly_detector()
    patch_segment_sorter()
    patch_leak_classifier()

    # Re-run the system
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.main import main as run_main
    run_main()


if __name__ == "__main__":
    main()
