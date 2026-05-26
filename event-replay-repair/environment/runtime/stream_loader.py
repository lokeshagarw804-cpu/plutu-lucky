"""Stream loader — reads event data from command stream JSON files.

Each stream file contains a sequence of domain events from a particular
command source (orders, payments, adjustments, refunds). Events are
loaded and tagged with their source stream identifier.
"""
import configparser
import json
import os


class StreamLoader:
    """Loads domain events from configured stream source files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("streams", "source_dir")
        raw_streams = self._config.get("streams", "included_streams")
        self._included = set(raw_streams.split(","))

    def load_streams(self):
        """Load all events from included stream files.

        Returns dict mapping stream_id to list of event dicts.
        Only streams listed in the included_streams config are loaded.
        """
        streams = {}
        for filename in os.listdir(self._source_dir):
            if not filename.endswith(".json"):
                continue
            stream_id = filename.replace(".json", "")
            if stream_id not in self._included:
                continue
            filepath = os.path.join(self._source_dir, filename)
            with open(filepath, "r") as f:
                data = json.load(f)
            streams[stream_id] = data["events"]
        return streams
