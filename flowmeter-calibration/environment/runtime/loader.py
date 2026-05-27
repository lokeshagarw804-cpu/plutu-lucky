"""Sensor data loader — reads meter JSON files from the data directory.

Loads all active meter files specified in the configuration and returns
structured reading data for downstream processing stages.
"""
import configparser
import json
import os


class MeterLoader:
    """Loads meter reading data from JSON files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._data_dir = self._config.get("meters", "data_dir")
        active = self._config.get("meters", "active_meters")
        self._active_meters = [m.strip() for m in active.split(",")]

    def load_meters(self):
        """Load all active meter data files.

        Returns dict mapping meter_id to full meter record including
        readings list, location, and metadata.
        """
        meters = {}
        for meter_id in self._active_meters:
            filepath = os.path.join(self._data_dir, f"{meter_id}.json")
            if not os.path.isfile(filepath):
                continue
            with open(filepath, "r") as f:
                data = json.load(f)
            meters[data["meter_id"]] = data
        return meters
