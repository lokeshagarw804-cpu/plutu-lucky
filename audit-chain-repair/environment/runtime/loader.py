"""Stream loader — reads audit log stream files from data directory.

Loads JSON-format stream files containing audit entries. Only
streams whose type appears in the active_streams configuration
are loaded for verification processing.
"""
import configparser
import json
import os


class StreamLoader:
    """Loads audit streams from data directory based on active config."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("streams", "source_dir")
        raw_streams = self._config.get("streams", "active_streams")
        self._active_streams = set(raw_streams.split(","))

    def load_streams(self):
        """Load all stream files and filter to active stream types.

        Returns dict mapping stream_id to stream data (with entries list).
        Only streams whose stream_type appears in active_streams are loaded.
        """
        streams = {}
        for fname in sorted(os.listdir(self._source_dir)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(self._source_dir, fname)
            with open(fpath, "r") as f:
                data = json.load(f)

            stream_type = data.get("stream_type", "")
            if stream_type in self._active_streams:
                streams[data["stream_id"]] = data

        return streams
