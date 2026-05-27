"""Fleet data loader — reads vehicle telemetry from JSON files."""
import configparser
import json
import os


class FleetLoader:
    """Loads raw telemetry data for configured vehicles."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._data_dir = self._config.get("fleet", "data_dir")
        raw_vehicles = self._config.get("fleet", "vehicles")
        self._vehicles = [v.strip() for v in raw_vehicles.split(",")]

    def load_vehicles(self):
        """Load telemetry feeds for all configured vehicles.

        Returns dict mapping vehicle_id to list of pings sorted by timestamp.
        """
        fleet = {}
        for vid in self._vehicles:
            path = os.path.join(self._data_dir, f"{vid}.json")
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                data = json.load(f)
            # Sort pings by timestamp
            pings = sorted(data["pings"], key=lambda p: p["timestamp"])
            fleet[vid] = {
                "vehicle_id": vid,
                "pings": pings,
            }
        return fleet
