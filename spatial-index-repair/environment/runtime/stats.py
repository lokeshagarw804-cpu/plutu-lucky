"""Statistics aggregator — computes index and spatial statistics.

Processes the R-tree nodes in partitions and computes per-category
counts, node utilization, and spatial distribution metrics.
"""
import configparser
import math


class StatisticsAggregator:
    """Computes statistics over the spatial index."""

    def __init__(self, config_path, indexer):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._indexer = indexer
        self._batch_size = self._config.getint("indexer", "batch_size")

    def compute_statistics(self):
        """Compute index statistics across all nodes."""
        nodes = self._indexer.get_nodes()
        all_entries = self._indexer.get_all_entries()

        # Compute per-category counts by scanning partitions
        category_counts = {}
        partition_size = self._batch_size

        for part_start in range(0, len(all_entries), partition_size):
            partition = all_entries[part_start:part_start + partition_size]
            partition_counts = {}
            for entry in partition:
                cat = entry["category"]
                partition_counts[cat] = partition_counts.get(cat, 0) + 1

            # Merge partition snapshot into totals
            for cat, count in partition_counts.items():
                category_counts[cat] = category_counts.get(cat, 0) + count

        # Node statistics
        node_count = len(nodes)
        entries_per_node = [len(n.entries) for n in nodes]
        avg_fill = sum(entries_per_node) / node_count if node_count > 0 else 0

        # Spatial spread
        all_lats = [e["lat"] for e in all_entries]
        all_lons = [e["lon"] for e in all_entries]
        lat_spread = max(all_lats) - min(all_lats) if all_lats else 0
        lon_spread = max(all_lons) - min(all_lons) if all_lons else 0

        return {
            "total_indexed": len(all_entries),
            "node_count": node_count,
            "avg_node_fill": round(avg_fill, 2),
            "max_entries_per_node": self._config.getint("indexer", "max_entries_per_node"),
            "category_counts": category_counts,
            "spatial_extent": {
                "lat_spread": round(lat_spread, 4),
                "lon_spread": round(lon_spread, 4),
            },
        }
