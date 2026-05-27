"""Graph loader — reads workflow DAG definition and resource data.

Parses the workflow graph JSON, resource allocation limits, and
priority override configurations from the data directory.
"""
import configparser
import json
import os


class WorkflowLoader:
    """Loads workflow DAG and associated resource/priority data."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._data_dir = os.path.dirname(config_path)
        self._data_dir = os.path.join(self._data_dir, "data")

    def load_graph(self):
        """Load the workflow DAG definition."""
        path = os.path.join(self._data_dir, "workflow_graph.json")
        with open(path, "r") as f:
            return json.load(f)

    def load_resources(self):
        """Load resource allocation limits per node."""
        path = os.path.join(self._data_dir, "resource_limits.json")
        with open(path, "r") as f:
            return json.load(f)

    def load_overrides(self):
        """Load priority boost overrides and decay settings."""
        path = os.path.join(self._data_dir, "priority_overrides.json")
        with open(path, "r") as f:
            return json.load(f)

    def get_priority_weights(self):
        """Build priority level to weight mapping from config.

        Priority levels are defined as a comma-separated list.
        Each level has a corresponding weight_<level> entry.
        """
        raw_levels = self._config.get("priorities", "levels")
        levels = set(raw_levels.split(","))
        weights = {}
        for level in levels:
            key = f"weight_{level}"
            if self._config.has_option("priorities", key):
                weights[level] = self._config.getint("priorities", key)
            else:
                weights[level] = self._config.getint("scheduler", "default_weight")
        return weights
