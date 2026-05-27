#!/usr/bin/env python3
"""Repair script for fleet telemetry engine."""
import sys


def patch_distance_calc():
    """Fix Haversine formula — dlat/dlon were swapped."""
    path = "/app/runtime/distance_calc.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "dlat = math.radians(lon2 - lon1)",
        "dlat = math.radians(lat2 - lat1)"
    )
    content = content.replace(
        "dlon = math.radians(lat2 - lat1)",
        "dlon = math.radians(lon2 - lon1)"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_trip_segmenter():
    """Fix threshold comparison — should be > not >=."""
    path = "/app/runtime/trip_segmenter.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "if gap >= self._idle_threshold:",
        "if gap > self._idle_threshold:"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_fuel_calculator():
    """Fix accumulator — should be += not =."""
    path = "/app/runtime/fuel_calculator.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "total_fuel = fuel_delta",
        "total_fuel += fuel_delta"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_scorer():
    """Fix weighted average denominator — use applicable weights only."""
    path = "/app/runtime/scorer.py"
    with open(path, "r") as f:
        content = f.read()

    old_block = """        total_weight = self._w_efficiency + self._w_speed + self._w_idle

        weighted_sum = 0.0
        if eff_score is not None:
            weighted_sum += self._w_efficiency * eff_score
        if speed_score is not None:
            weighted_sum += self._w_speed * speed_score
        if idle_score is not None:
            weighted_sum += self._w_idle * idle_score

        return round(weighted_sum / total_weight, 4)"""

    new_block = """        weighted_sum = 0.0
        total_weight = 0.0
        if eff_score is not None:
            weighted_sum += self._w_efficiency * eff_score
            total_weight += self._w_efficiency
        if speed_score is not None:
            weighted_sum += self._w_speed * speed_score
            total_weight += self._w_speed
        if idle_score is not None:
            weighted_sum += self._w_idle * idle_score
            total_weight += self._w_idle

        if total_weight == 0:
            return 0.0
        return round(weighted_sum / total_weight, 4)"""

    content = content.replace(old_block, new_block)

    with open(path, "w") as f:
        f.write(content)


def patch_aggregator():
    """Fix vehicle ordering — sort by numeric suffix."""
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "vehicle_ids = sorted(vehicle_results.keys())",
        "vehicle_ids = sorted(vehicle_results.keys(), key=lambda v: int(v[1:]))"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_distance_calc()
    patch_trip_segmenter()
    patch_fuel_calculator()
    patch_scorer()
    patch_aggregator()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.main import main as run_main
    run_main()


if __name__ == "__main__":
    main()
