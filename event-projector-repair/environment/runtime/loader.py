"""Aggregate event loader — reads event streams from data directory.

Loads JSON-format aggregate files containing domain events. Only
aggregates whose type appears in the active_types configuration
are loaded for replay processing.
"""
import configparser
import json
import os


class AggregateLoader:
    """Loads aggregate event streams from data directory."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("aggregates", "source_dir")
        raw_types = self._config.get("aggregates", "active_types")
        self._active_types = set(raw_types.split(","))

    def load_aggregates(self):
        """Load all aggregate files and filter to active types.

        Returns dict mapping aggregate_id to aggregate data.
        Only aggregates whose type appears in active_types are loaded.
        """
        aggregates = {}
        for fname in sorted(os.listdir(self._source_dir)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(self._source_dir, fname)
            with open(fpath, "r") as f:
                data = json.load(f)

            agg_type = data.get("aggregate_type", "")
            if agg_type in self._active_types:
                aggregates[data["aggregate_id"]] = data

        return aggregates
