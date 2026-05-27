"""Fleet data loader — reads vehicle telemetry feeds from JSON files."""
import configparser
import json
import os


class FleetLoader:
    """Loads raw telemetry data for configured fleet vehicles."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._data_dir = self._config.get("fleet", "data_dir")
        raw_vehicles = self._config.get("fleet", "vehicles")
        self._active = [v.strip() for v in raw_vehicles.split(",")]

    def load_vehicles(self):
        """Load telemetry data for all active vehicles.

        Returns dict mapping vehicle_id to data dict with readings.
        """
        vehicles = {}
        for vehicle_id in self._active:
            path = os.path.join(self._data_dir, f"{vehicle_id}.json")
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                data = json.load(f)
            vehicles[vehicle_id] = {
                "vehicle_id": vehicle_id,
                "sample_interval": data["sample_interval"],
                "start_epoch": data["start_epoch"],
                "readings": data["readings"],
            }
        return vehicles
