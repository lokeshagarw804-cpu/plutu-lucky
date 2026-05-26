#!/usr/bin/env python3
"""Repair script for geofence alert engine.

Patches defects in runtime source files and re-runs the system.
"""
import sys


def patch_geofence():
    """Fix point-in-polygon boundary condition.

    The ray-casting test uses lon <= intersect_lon which incorrectly
    counts edge-coincident points. Must use strict < for the ray
    crossing test and add explicit horizontal edge inclusion.
    """
    path = "/app/runtime/geofence.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix the ray intersection comparison
    content = content.replace(
        "if lon <= intersect_lon:\n                    inside = not inside",
        "if lon < intersect_lon:\n                    inside = not inside"
    )

    # Add horizontal edge handling before j = i
    old_block = "            j = i\n\n        return inside"
    new_block = (
        "            # Handle point lying exactly on a horizontal edge\n"
        "            elif lat_i == lat == lat_j:\n"
        "                if min(lon_i, lon_j) <= lon <= max(lon_i, lon_j):\n"
        "                    return True\n"
        "            j = i\n\n        return inside"
    )
    content = content.replace(old_block, new_block)

    with open(path, "w") as f:
        f.write(content)


def patch_tracker():
    """Fix state machine confirmation counter reset.

    The ENTERING state handler resets confirm_counter to 0 before
    incrementing, so it never reaches the confirmation threshold.
    Remove the spurious reset.
    """
    path = "/app/runtime/tracker.py"
    with open(path, "r") as f:
        content = f.read()

    # Remove the counter reset in ENTERING state
    old_entering = (
        "        elif current_state == self.ENTERING:\n"
        "            state_info[\"confirm_counter\"] = 0\n"
        "            if is_inside:\n"
        "                state_info[\"confirm_counter\"] += 1"
    )
    new_entering = (
        "        elif current_state == self.ENTERING:\n"
        "            if is_inside:\n"
        "                state_info[\"confirm_counter\"] += 1"
    )
    content = content.replace(old_entering, new_entering)

    with open(path, "w") as f:
        f.write(content)


def patch_alerts():
    """Fix weight accumulator and sort key.

    1. total_weight overwrites with each zone's weight instead of
       accumulating. Must use += for correct weighted average.
    2. Sort key missing vehicle_id tiebreaker for deterministic
       ordering when severities are equal.
    """
    path = "/app/runtime/alerts.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix weight accumulation (= should be +=)
    content = content.replace(
        "total_weight = weight",
        "total_weight += weight"
    )

    # Fix sort key to include vehicle_id
    content = content.replace(
        'alerts.sort(key=lambda a: (a["zone_id"], -a["severity"]))',
        'alerts.sort(key=lambda a: (a["zone_id"], -a["severity"], a["vehicle_id"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_geofence()
    patch_tracker()
    patch_alerts()

    # Re-run with patched code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.main import main as run_main
    run_main()


if __name__ == "__main__":
    main()
