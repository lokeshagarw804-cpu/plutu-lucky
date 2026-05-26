"""
Grid partitioning module.

Assigns sensor readings to grid cells based on their geographic
coordinates. The grid covers a defined extent with uniform cell size.
"""

import configparser


class GridPartitioner:
    """Partitions readings into grid cells."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._cell_size = config.getfloat("grid", "cell_size")
        self._origin_lat = config.getfloat("grid", "origin_lat")
        self._origin_lon = config.getfloat("grid", "origin_lon")
        self._rows = config.getint("grid", "grid_rows")
        self._cols = config.getint("grid", "grid_cols")

    def assign_cells(self, readings):
        """Assign each reading to a grid cell based on coordinates.

        Returns readings augmented with cell_row and cell_col fields.
        Readings outside the grid extent are excluded.
        """
        assigned = []
        for reading in readings:
            lat = reading["latitude"]
            lon = reading["longitude"]

            row = int((lat - self._origin_lat) / self._cell_size)
            col = int((lon - self._origin_lon) / self._cell_size)

            if 0 <= row < self._rows and 0 <= col < self._cols:
                assigned.append({
                    **reading,
                    "cell_row": row,
                    "cell_col": col,
                    "cell_id": f"R{row:02d}C{col:02d}",
                })

        return assigned
