#!/usr/bin/env python3
"""Repair script for spatial grid indexer. Patches all defects and re-runs."""
import os
import sys


def patch_loader():
    """Fix Bug A: strip whitespace from comma-split layer type list."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._active_layers = set(raw_layers.split(","))',
        'self._active_layers = set(t.strip() for t in raw_layers.split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_grid_indexer():
    """Fix Bug B: read resolution from grid.analysis section."""
    path = "/app/runtime/grid_indexer.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._resolution = self._config.getint("grid", "resolution")',
        'self._resolution = self._config.getint("grid.analysis", "resolution")'
    )

    content = content.replace(
        "self._cell_size = self._extent_x / self._resolution",
        "self._cell_size = self._config.getfloat(\"grid.analysis\", \"cell_size\")"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_density_calculator():
    """Fix Bug C: average density across passes instead of accumulating."""
    path = "/app/runtime/density_calculator.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "            # Final density: accumulated across passes (should be average)\n"
        "            densities[cell_key] = round(running_density, 4)",
        "            # Final density: average across passes\n"
        "            densities[cell_key] = round(running_density / self._passes, 4)"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_run_spatial():
    """Fix Bug D: add layer_id as tiebreaker in point sort."""
    path = "/app/runtime/run_spatial.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'all_points.sort(key=lambda p: (p["timestamp"], p["seq"]))',
        'all_points.sort(key=lambda p: (p["timestamp"], p["layer_id"], p["seq"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_grid_indexer()
    patch_density_calculator()
    patch_run_spatial()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_spatial import main as run_main
    run_main()


if __name__ == "__main__":
    main()
