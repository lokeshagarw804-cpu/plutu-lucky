"""Source loader — reads geographic feature records from JSON data files."""
import configparser
import json
import os


class SourceLoader:
    """Loads geographic feature data from configured source files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._data_dir = self._config.get("sources", "data_dir")
        raw_sources = self._config.get("sources", "active_sources")
        self._active = set(raw_sources.split(","))

    def load_sources(self):
        """Load feature records for all active sources.

        Returns dict mapping source_id to list of feature records.
        """
        sources = {}
        for filename in os.listdir(self._data_dir):
            if not filename.endswith(".json"):
                continue
            source_id = filename.replace(".json", "")
            if source_id not in self._active:
                continue
            path = os.path.join(self._data_dir, filename)
            with open(path, "r") as f:
                data = json.load(f)
            sources[source_id] = data["features"]
        return sources
