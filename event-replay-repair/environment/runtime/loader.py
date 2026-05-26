"""Event stream loader. Reads JSON event files from the data directory."""
import json
import os
import configparser


class EventLoader:
    """Loads event streams from disk based on configuration."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_streams = self._config.get("sources", "event_streams")
        self._allowed = set(raw_streams.split(","))
        self._data_dir = "/app/runtime/data"

    def load_all(self):
        """Load all events from allowed streams."""
        all_events = []
        for filename in sorted(os.listdir(self._data_dir)):
            if not filename.endswith(".json"):
                continue
            stream_name = filename.replace("stream_", "").replace(".json", "")
            if stream_name not in self._allowed:
                continue
            filepath = os.path.join(self._data_dir, filename)
            with open(filepath, "r") as f:
                events = json.load(f)
            all_events.extend(events)
        return all_events

    @property
    def allowed_streams(self):
        return self._allowed
