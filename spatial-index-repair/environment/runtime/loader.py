"""Signal loader — reads station time-series data from JSON files."""
import configparser
import json
import os


class SignalLoader:
    """Loads raw signal data from station JSON files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("signals", "source_dir")
        raw_stations = self._config.get("stations", "active_stations")
        self._active = [s.strip() for s in raw_stations.split(",")]

    def load_stations(self):
        """Load signal data for all active stations."""
        stations = {}
        for station_id in self._active:
            path = os.path.join(self._source_dir, f"{station_id}.json")
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                data = json.load(f)
            stations[station_id] = {
                "station_id": station_id,
                "sample_rate": data["sample_rate"],
                "start_time": data["start_time"],
                "values": data["values"],
            }
        return stations
