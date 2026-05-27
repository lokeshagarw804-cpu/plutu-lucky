"""Stream loader — reads event stream data from JSON source files.

Each stream file contains an ordered sequence of domain events with
timestamps, sequence numbers (local to that stream), and typed payloads.
"""
import configparser
import json
import os


class StreamLoader:
    """Loads event streams from configured source directory."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("streams", "source_dir")
        raw_streams = self._config.get("streams", "active_streams")
        self._active = set(raw_streams.split(","))

    def load_streams(self):
        """Load all active stream files and return as dict of stream_id -> events."""
        streams = {}
        for stream_id in self._active:
            path = os.path.join(self._source_dir, f"{stream_id}.json")
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                data = json.load(f)
            events = []
            for evt in data["events"]:
                events.append({
                    "event_id": evt["event_id"],
                    "timestamp": evt["timestamp"],
                    "sequence": evt["sequence"],
                    "stream_id": data["stream_id"],
                    "type": evt["type"],
                    "entity_id": evt["entity_id"],
                    "payload": evt["payload"],
                })
            streams[data["stream_id"]] = events
        return streams
