#!/usr/bin/env python3
"""Repair script for the spatial grid indexing system."""
import os
import sys


def patch_partitioner():
    """Fix Bug A: int() truncation vs floor division for negative coords."""
    path = "/app/runtime/grid_partitioner.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'row = int((lat - self._origin_lat) / self._cell_size)',
        'row = int((lat - self._origin_lat) // self._cell_size)'
    )
    content = content.replace(
        'col = int((lon - self._origin_lon) / self._cell_size)',
        'col = int((lon - self._origin_lon) // self._cell_size)'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_aggregator():
    """Fix Bug B: population variance (N) vs sample variance (N-1)."""
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        "variance = sum((v - mean) ** 2 for v in values) / n",
        "variance = sum((v - mean) ** 2 for v in values) / (n - 1)"
    )
    with open(path, "w") as f:
        f.write(content)


def patch_cluster_finder():
    """Fix Bug C: 4-connectivity instead of 8-connectivity."""
    path = "/app/runtime/cluster_finder.py"
    with open(path, "r") as f:
        content = f.read()
    old_neighbors = '''        neighbors = [
            (row - 1, col), (row + 1, col),
            (row, col - 1), (row, col + 1),
        ]
        return neighbors'''
    new_neighbors = '''        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                neighbors.append((row + dr, col + dc))
        return neighbors'''
    content = content.replace(old_neighbors, new_neighbors)
    with open(path, "w") as f:
        f.write(content)


def patch_query_engine():
    """Fix Bug D: filter readings before aggregation instead of after."""
    path = "/app/runtime/query_engine.py"
    with open(path, "r") as f:
        content = f.read()
    # Replace the method to query by cell center distance, not individual reading distance
    old_query = '''    def execute_query(self, assigned_readings, cell_stats):
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
        return results[:self._max_results]'''
    new_query = '''    def execute_query(self, assigned_readings, cell_stats):
        """Find cells within radius of query center.

        Returns cell statistics for cells whose center falls within
        the query radius, ranked by reading count descending.
        """
        results = []
        for cell_id, stats in cell_stats.items():
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
            if dist <= self._radius:
                results.append({
                    **stats,
                    "distance": round(dist, 4),
                })

        results.sort(key=lambda r: (-r["count"], r["distance"]))
        return results[:self._max_results]'''
    content = content.replace(old_query, new_query)
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_partitioner()
    patch_aggregator()
    patch_cluster_finder()
    patch_query_engine()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_spatial import main as run_main
    run_main()


if __name__ == "__main__":
    main()
