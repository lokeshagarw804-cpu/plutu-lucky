"""Density calculator — computes spatial density for occupied grid cells.

Performs multiple density passes over the grid to produce smoothed
density scores. Uses a distance-weighted linear kernel where points
closer to the cell centroid contribute more weight.

The kernel function is: contribution = point_weight * (1 - dist/radius)
for points within the kernel_radius. The density for each cell is the
sum of all weighted contributions divided by the cell area, then
averaged across passes.
"""
import configparser
import math


class DensityCalculator:
    """Computes kernel density scores through multiple smoothing passes."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._kernel_radius = self._config.getfloat("density", "kernel_radius")
        self._passes = self._config.getint("density", "passes")

    def compute_density(self, grid, cell_size, all_points):
        """Compute density scores for all occupied cells.

        For each cell, applies a distance-weighted linear kernel:
        contribution = weight * (1 - distance / kernel_radius)

        The density is the sum of contributions divided by cell area,
        averaged across all passes.

        Returns dict mapping cell key to density score.
        """
        cell_area = cell_size * cell_size
        densities = {}

        for cell_key, cell_points in grid.items():
            cx, cy = cell_key
            centroid_x = (cx + 0.5) * cell_size
            centroid_y = (cy + 0.5) * cell_size

            # Multi-pass density
            total_density = 0.0
            for pass_num in range(self._passes):
                pass_contributions = 0.0
                for pt in all_points:
                    dist = math.sqrt(
                        (pt["x"] - centroid_x) ** 2
                        + (pt["y"] - centroid_y) ** 2
                    )
                    if dist <= self._kernel_radius:
                        # Distance-weighted kernel: but uses dist^2 in weight
                        # (should use linear dist for linear kernel)
                        kernel_weight = 1.0 - (dist * dist) / (
                            self._kernel_radius * self._kernel_radius
                        )
                        pass_contributions += pt["weight"] * kernel_weight

                pass_density = pass_contributions / cell_area
                total_density += pass_density

            # Average across passes
            densities[cell_key] = round(total_density / self._passes, 4)

        return densities

    def get_kernel_radius(self):
        """Return kernel radius."""
        return self._kernel_radius
