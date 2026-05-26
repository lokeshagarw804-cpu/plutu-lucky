"""
Hotspot cluster identification.

Identifies clusters of adjacent high-density grid cells.
Uses connected-component analysis on the cell grid.
"""

import configparser
from collections import deque


class ClusterFinder:
    """Finds clusters of dense cells."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._density_threshold = config.getint(
            "clustering", "density_threshold"
        )
        self._connectivity = config.getint("clustering", "connectivity")
        self._min_cluster_size = config.getint(
            "clustering", "min_cluster_size"
        )

    def find_clusters(self, cell_stats):
        """Find clusters of adjacent dense cells.

        A cell is 'dense' if its reading count meets the threshold.
        Adjacent dense cells form a cluster via connected components.
        """
        dense_cells = set()
        for cell_id, stats in cell_stats.items():
            if stats["count"] >= self._density_threshold:
                dense_cells.add((stats["cell_row"], stats["cell_col"]))

        visited = set()
        clusters = []

        for cell in dense_cells:
            if cell in visited:
                continue
            cluster = self._bfs_cluster(cell, dense_cells, visited)
            if len(cluster) >= self._min_cluster_size:
                clusters.append(cluster)

        return self._format_clusters(clusters, cell_stats)

    def _bfs_cluster(self, start, dense_cells, visited):
        """BFS to find connected component of dense cells."""
        queue = deque([start])
        visited.add(start)
        component = [start]

        while queue:
            row, col = queue.popleft()
            for nr, nc in self._get_neighbors(row, col):
                if (nr, nc) in dense_cells and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    component.append((nr, nc))
                    queue.append((nr, nc))

        return component

    def _get_neighbors(self, row, col):
        """Get neighboring cells using configured connectivity.

        4-connectivity: up, down, left, right only.
        8-connectivity: includes diagonal neighbors.
        """
        neighbors = [
            (row - 1, col), (row + 1, col),
            (row, col - 1), (row, col + 1),
        ]
        return neighbors

    def _format_clusters(self, clusters, cell_stats):
        """Format cluster data for output."""
        result = []
        for i, cells in enumerate(clusters):
            cell_ids = [f"R{r:02d}C{c:02d}" for r, c in cells]
            total_readings = sum(
                cell_stats.get(cid, {}).get("count", 0)
                for cid in cell_ids
            )
            result.append({
                "cluster_id": i,
                "cell_count": len(cells),
                "cells": sorted(cell_ids),
                "total_readings": total_readings,
            })
        return sorted(result, key=lambda c: -c["total_readings"])
