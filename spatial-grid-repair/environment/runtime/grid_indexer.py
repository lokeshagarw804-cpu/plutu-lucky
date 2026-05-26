"""Grid indexer — assigns points to grid cells based on coordinates.

Maps each point to its corresponding grid cell using the configured
resolution from the grid.analysis section. Cell assignment uses floor
division of coordinates by cell_size.

The grid uses cells of size (extent / resolution). A point at coordinate
x is assigned to cell floor(x / cell_size). Points exactly on the upper
boundary of a cell (x == cell_boundary) belong to that cell (inclusive
upper bound), not the next cell.
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
        self._cell_size = self._extent_x / self._resolution

    def index_points(self, all_points):
        """Assign each point to a grid cell.

        Cell coordinates are computed as floor(point_coord / cell_size).
        Points on cell boundaries (coord == boundary) are assigned to
        the cell below (inclusive upper bound).

        Returns dict mapping (cell_x, cell_y) to list of point records.
        """
        grid = {}

        for point in all_points:
            cx = self._get_cell(point["x"], self._extent_x)
            cy = self._get_cell(point["y"], self._extent_y)
            key = (cx, cy)
            if key not in grid:
                grid[key] = []
            grid[key].append(point)

        return grid

    def _get_cell(self, coord, extent):
        """Compute cell index for a coordinate.

        Points exactly on a cell boundary should be assigned to the
        lower cell (inclusive upper bound). Maximum cell index is
        resolution - 1.
        """
        cell = int(coord / self._cell_size)
        # Boundary: points at exact multiples of cell_size
        # go to previous cell (upper bound inclusive)
        if coord > 0 and coord % self._cell_size == 0 and cell > 0:
            cell -= 1
        return min(cell, self._resolution - 1)

    def get_resolution(self):
        """Return grid resolution."""
        return self._resolution

    def get_cell_size(self):
        """Return cell size."""
        return self._cell_size
