"""R-tree spatial indexer — builds a spatial index from POI records.

Processes records in batches, assigns them to leaf nodes using a
quadratic-split algorithm simulation, and maintains the index structure.
"""
import configparser
import math


class RTreeNode:
    """A node in the R-tree index."""

    def __init__(self, node_id, level=0):
        self.node_id = node_id
        self.level = level
        self.entries = []
        self.bounds = None

    def update_bounds(self):
        if not self.entries:
            self.bounds = None
            return
        lats = [e["lat"] for e in self.entries]
        lons = [e["lon"] for e in self.entries]
        self.bounds = {
            "lat_min": min(lats),
            "lat_max": max(lats),
            "lon_min": min(lons),
            "lon_max": max(lons),
        }


class RTreeIndexer:
    """Builds and queries an R-tree spatial index."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._batch_size = self._config.getint("indexer", "batch_size")
        self._max_entries = self._config.getint("indexer", "max_entries_per_node")
        self._nodes = []
        self._all_entries = []
        self._node_counter = 0

    def build_index(self, records):
        """Build the R-tree index from sorted records."""
        # Sort records for deterministic insertion order
        # Note: seq is local to each feed stream
        sorted_records = sorted(
            records, key=lambda r: (r["timestamp"], r["seq"])
        )
        self._all_entries = sorted_records

        # Process in batches
        for batch_start in range(0, len(sorted_records), self._batch_size):
            batch = sorted_records[batch_start:batch_start + self._batch_size]
            self._insert_batch(batch)

    def _insert_batch(self, batch):
        """Insert a batch of records into the index."""
        current_node = self._get_or_create_node()
        for record in batch:
            entry = {
                "name": record["name"],
                "category": record["category"],
                "lat": record["lat"],
                "lon": record["lon"],
                "feed_id": record["feed_id"],
                "seq": record["seq"],
                "timestamp": record["timestamp"],
            }
            current_node.entries.append(entry)
            if len(current_node.entries) >= self._max_entries:
                current_node.update_bounds()
                current_node = self._get_or_create_node()
        current_node.update_bounds()

    def _get_or_create_node(self):
        """Get current leaf node or create a new one."""
        if not self._nodes or len(self._nodes[-1].entries) >= self._max_entries:
            self._node_counter += 1
            node = RTreeNode(self._node_counter, level=0)
            self._nodes.append(node)
        return self._nodes[-1]

    def query_region(self, lat_min, lat_max, lon_min, lon_max):
        """Query all entries within the given bounding box."""
        results = []
        for node in self._nodes:
            if node.bounds is None:
                continue
            if self._intersects(node.bounds, lat_min, lat_max, lon_min, lon_max):
                for entry in node.entries:
                    if (lat_min <= entry["lat"] <= lat_max and
                            lon_min <= entry["lon"] <= lon_max):
                        results.append(entry)
        return results

    def _intersects(self, bounds, lat_min, lat_max, lon_min, lon_max):
        """Check if node bounds intersect query region."""
        return not (
            bounds["lat_max"] < lat_min or
            bounds["lat_min"] > lat_max or
            bounds["lon_max"] < lon_min or
            bounds["lon_min"] > lon_max
        )

    def get_nodes(self):
        """Return all index nodes with entries."""
        return [n for n in self._nodes if n.entries]

    def get_all_entries(self):
        """Return all indexed entries in insertion order."""
        return self._all_entries
