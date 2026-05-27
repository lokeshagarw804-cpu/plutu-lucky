"""Event stream loader — reads transaction event data from JSON files.

Loads event streams from the configured source directory, filtering
by active account types defined in configuration.
"""
import configparser
import json
import os


class EventStreamLoader:
    """Loads event streams from JSON source files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("ledger", "source_dir")
        raw_types = self._config.get("accounts", "active_types")
        self._active_types = set(raw_types.split(","))

    def load_streams(self):
        """Load all event streams matching active account types.

        Returns dict mapping stream_id to stream data including events.
        """
        streams = {}
        source_dir = self._source_dir

        for filename in sorted(os.listdir(source_dir)):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(source_dir, filename)
            with open(filepath, "r") as f:
                data = json.load(f)

            account_type = data.get("account_type", "")
            if account_type not in self._active_types:
                continue

            stream_id = data["stream_id"]
            streams[stream_id] = {
                "stream_id": stream_id,
                "account_type": account_type,
                "owner": data["owner"],
                "events": data["events"],
            }

        return streams
