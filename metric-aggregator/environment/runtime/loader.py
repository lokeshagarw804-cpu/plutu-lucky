"""Metric loader — reads service node performance data from JSON files."""
import configparser
import json
import os


class MetricLoader:
    """Loads raw metric data from service node JSON files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("services", "source_dir")
        raw_nodes = self._config.get("services", "active_nodes")
        self._active = [s.strip() for s in raw_nodes.split(",")]

    def load_nodes(self):
        """Load metric data for all active service nodes.

        Returns dict mapping node_id to node data including metrics
        and metadata (region, start_epoch, interval_sec).
        """
        nodes = {}
        for node_id in self._active:
            path = os.path.join(self._source_dir, f"{node_id}.json")
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                data = json.load(f)
            nodes[node_id] = {
                "node_id": node_id,
                "region": data["region"],
                "start_epoch": data["start_epoch"],
                "interval_sec": data["interval_sec"],
                "metrics": data["metrics"],
            }
        return nodes
