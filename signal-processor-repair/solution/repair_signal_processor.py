#!/usr/bin/env python3
"""Repair script for the signal processing system."""
import os
import sys


def patch_normalizer_filter():
    """Fix Bug A: calibrated_ids parsing does not strip whitespace."""
    path = "/app/runtime/normalizer.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._station_ids = set(raw_ids.split(","))',
        'self._station_ids = set(s.strip() for s in raw_ids.split(","))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_normalizer_calibration():
    """Fix Bug E: calibration uses multiplication instead of addition."""
    path = "/app/runtime/normalizer.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        "cal_value = raw * offset",
        "cal_value = raw + offset"
    )
    with open(path, "w") as f:
        f.write(content)


def patch_detector_threshold():
    """Fix Bug B: detector reads from wrong config section."""
    path = "/app/runtime/event_detector.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._noise_threshold = config.getfloat(\n            "detection", "noise_threshold"\n        )',
        'self._noise_threshold = config.getfloat(\n            "detection.refined", "noise_threshold"\n        )'
    )
    content = content.replace(
        'self._window_size = config.getint("detection", "window_size")',
        'self._window_size = config.getint("detection.refined", "window_size")'
    )
    content = content.replace(
        'self._min_readings = config.getint(\n            "detection", "min_readings_per_window"\n        )',
        'self._min_readings = config.getint(\n            "detection.refined", "min_readings_per_window"\n        )'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_correlator():
    """Fix Bug C: correlation matrix reports total instead of average."""
    path = "/app/runtime/correlator.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        '"avg_correlation": round(total, 6),',
        '"avg_correlation": round(total / count, 6),'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_sort_order():
    """Fix Bug D: anomaly sort missing station_id tiebreaker."""
    path = "/app/runtime/matrix_builder.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'key=lambda a: (-a["severity_score"], a["timestamp"])',
        'key=lambda a: (-a["severity_score"], a["station_id"], a["timestamp"])'
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_normalizer_filter()
    patch_normalizer_calibration()
    patch_detector_threshold()
    patch_correlator()
    patch_sort_order()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_spatial import main as run_main
    run_main()


if __name__ == "__main__":
    main()
