"""Grid indexer — assigns points to grid cells based on coordinates.

Maps each point to its corresponding grid cell using the configured
resolution from the grid.analysis section. The cell_size parameter
from that section defines the physical size of each cell.

Cell assignment: a point at coordinate x goes to cell floor(x / cell_size).
Points exactly on the upper boundary of a cell (x == cell_boundary) should
be assigned to that cell (the lower cell), not the next one. This ensures
boundary points remain in the correct neighborhood for density calculation.
"""
import configparser
import math


class GridIndexer:
    """Assigns spatial points to grid cells."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._resolution = self._config.getint("grid", "resolution")
        self._extent_x = self._config.getfloat("grid", "extent_x")
        self._extent_y = self._config.getfloat("grid", "extent_y")
        # Derive cell size from extent and resolution
        self._cell_size = self._extent_x / self._resolution

    def index_points(self, all_points):
        """Assign each point to a grid cell.

        Cell coordinates are computed as floor(point_coord / cell_size).
        Returns dict mapping (cell_x, cell_y) to list of point records.
        """
        grid = {}

        for point in all_points:
            cx = self._get_cell(point["x"])
            cy = self._get_cell(point["y"])
            key = (cx, cy)
            if key not in grid:
                grid[key] = []
            grid[key].append(point)

        return grid

    def _get_cell(self, coord):
        """Compute cell index for a coordinate.

        Uses floor division. Points on exact cell boundaries
        are handled by the floor operation naturally.
        """
        cell = int(coord / self._cell_size)
        return min(cell, self._resolution - 1)

    def get_resolution(self):
        """Return grid resolution."""
        return self._resolution

    def get_cell_size(self):
        """Return cell size."""
        return self._cell_size
