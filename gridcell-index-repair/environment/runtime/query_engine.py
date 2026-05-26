"""
Spatial query engine.

Executes range queries against the grid index to find cells
within a specified radius of a query point.
"""

import configparser
import math


class QueryEngine:
    """Executes spatial range queries."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._center_lat = config.getfloat("query", "center_lat")
        self._center_lon = config.getfloat("query", "center_lon")
        self._radius = config.getfloat("query", "radius")
        self._max_results = config.getint("query", "max_results")
        self._cell_size = config.getfloat("grid", "cell_size")
        self._origin_lat = config.getfloat("grid", "origin_lat")
        self._origin_lon = config.getfloat("grid", "origin_lon")

    def execute_query(self, assigned_readings, cell_stats):
        """Find cells within radius of query center.

        Filters readings by distance, then returns matching cell
        statistics ranked by reading count descending.
        """
        nearby_readings = []
        for reading in assigned_readings:
            dist = self._distance(
                reading["latitude"], reading["longitude"],
                self._center_lat, self._center_lon
            )
            if dist <= self._radius:
                nearby_readings.append(reading)

        nearby_cells = set(r["cell_id"] for r in nearby_readings)

        results = []
        for cell_id in nearby_cells:
            if cell_id in cell_stats:
                stats = cell_stats[cell_id]
                cell_center_lat = (
                    self._origin_lat +
                    (stats["cell_row"] + 0.5) * self._cell_size
                )
                cell_center_lon = (
                    self._origin_lon +
                    (stats["cell_col"] + 0.5) * self._cell_size
                )
                dist = self._distance(
                    cell_center_lat, cell_center_lon,
                    self._center_lat, self._center_lon
                )
                results.append({
                    **stats,
                    "distance": round(dist, 4),
                })

        results.sort(key=lambda r: (-r["count"], r["distance"]))
        return results[:self._max_results]

    def _distance(self, lat1, lon1, lat2, lon2):
        """Euclidean distance between two points."""
        return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)
