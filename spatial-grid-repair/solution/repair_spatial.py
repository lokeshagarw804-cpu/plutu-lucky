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
    """Fix Bug B: read resolution and cell_size from grid.analysis section."""
    path = "/app/runtime/grid_indexer.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix resolution source
    content = content.replace(
        'self._resolution = self._config.getint("grid", "resolution")',
        'self._resolution = self._config.getint("grid.analysis", "resolution")'
    )

    # Fix cell_size: read from config instead of deriving from extent
    content = content.replace(
        "self._cell_size = self._extent_x / self._resolution",
        'self._cell_size = self._config.getfloat("grid.analysis", "cell_size")'
    )

    # Fix boundary handling: exact multiples go to lower cell
    old_get_cell = '''    def _get_cell(self, coord):
        """Compute cell index for a coordinate.

        Uses floor division. Points on exact cell boundaries
        are handled by the floor operation naturally.
        """
        cell = int(coord / self._cell_size)
        return min(cell, self._resolution - 1)'''

    new_get_cell = '''    def _get_cell(self, coord):
        """Compute cell index for a coordinate.

        Uses floor division. Points on exact cell boundaries
        go to the lower cell (inclusive upper bound).
        """
        cell = int(coord / self._cell_size)
        if coord > 0 and abs(coord % self._cell_size) < 1e-9 and cell > 0:
            cell -= 1
        return min(cell, self._resolution - 1)'''

    content = content.replace(old_get_cell, new_get_cell)

    with open(path, "w") as f:
        f.write(content)


def patch_density_calculator():
    """Fix Bug C: use linear kernel weight, not quadratic."""
    path = "/app/runtime/density_calculator.py"
    with open(path, "r") as f:
        content = f.read()

    # Replace quadratic kernel with linear kernel
    content = content.replace(
        "                        # Distance-weighted kernel: but uses dist^2 in weight\n"
        "                        # (should use linear dist for linear kernel)\n"
        "                        kernel_weight = 1.0 - (dist * dist) / (\n"
        "                            self._kernel_radius * self._kernel_radius\n"
        "                        )",
        "                        # Linear distance-weighted kernel\n"
        "                        kernel_weight = 1.0 - dist / self._kernel_radius"
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
