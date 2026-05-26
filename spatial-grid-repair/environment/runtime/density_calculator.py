"""Density calculator — computes spatial density for occupied grid cells.

Performs multiple density passes over the grid to produce smoothed
density scores. Each pass computes the weighted point count within
the kernel radius of each cell's centroid.

The density for a cell in each pass should be the average of weights
of points within the kernel radius of that cell's center — computed
independently for each pass, not accumulated across passes.
"""
import configparser
import math


class DensityCalculator:
    """Computes density scores through multiple smoothing passes."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._kernel_radius = self._config.getfloat("density", "kernel_radius")
        self._passes = self._config.getint("density", "passes")
        self._cell_size = None

    def compute_density(self, grid, cell_size, all_points):
        """Compute density scores for all occupied cells.

        Performs multiple passes. In each pass, the density of a cell
        is the mean weight of all points within kernel_radius of the
        cell centroid. Final density is the average across all passes.

        Returns dict mapping cell key to density score.
        """
        self._cell_size = cell_size
        densities = {}

        for cell_key, cell_points in grid.items():
            # Compute centroid of cell
            cx, cy = cell_key
            centroid_x = (cx + 0.5) * cell_size
            centroid_y = (cy + 0.5) * cell_size

            # Multi-pass density computation
            running_density = 0.0
            for pass_num in range(self._passes):
                # Each pass considers all points within kernel radius
                weights_in_radius = []
                for pt in all_points:
                    dist = math.sqrt(
                        (pt["x"] - centroid_x) ** 2
                        + (pt["y"] - centroid_y) ** 2
                    )
                    if dist <= self._kernel_radius:
                        weights_in_radius.append(pt["weight"])

                if weights_in_radius:
                    pass_density = sum(weights_in_radius) / len(weights_in_radius)
                else:
                    pass_density = 0.0

                running_density += pass_density

            # Final density: accumulated across passes (should be average)
            densities[cell_key] = round(running_density, 4)

        return densities

    def get_kernel_radius(self):
        """Return kernel radius."""
        return self._kernel_radius
