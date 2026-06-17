"""Event stream loader — reads aggregate event streams from JSON files."""
import configparser
import json
import os


class StreamLoader:
    """Loads event streams for configured aggregates."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("streams", "source_dir")
        raw_aggregates = self._config.get("streams", "active_aggregates")
        self._active = set(raw_aggregates.split(","))

    def load_streams(self):
        """Load event data for all active aggregate streams."""
        streams = {}
        for filename in os.listdir(self._source_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self._source_dir, filename)
            with open(path, "r") as f:
                data = json.load(f)
            stream_id = data["stream_id"]
            if stream_id in self._active:
                streams[stream_id] = data
        return streams
