"""Telemetry loader — reads vehicle sensor streams from JSONL files.

Each line is a JSON object with ts (timestamp), sensor (sensor name),
and value (reading). Data is grouped by vehicle then by sensor.
"""
import configparser
import json
import os


class TelemetryLoader:
    """Loads raw telemetry readings from JSONL data files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._data_dir = self._config.get("pipeline", "data_dir")
        raw_fleet = self._config.get("vehicles", "fleet")
        self._fleet = [v.strip() for v in raw_fleet.split(",")]

    def load_fleet(self):
        """Load all vehicle telemetry grouped by vehicle and sensor.

        Returns dict: {vehicle_id: {sensor_name: [(ts, value), ...]}}
        """
        fleet_data = {}
        for vehicle_id in self._fleet:
            path = os.path.join(self._data_dir, f"{vehicle_id}.jsonl")
            if not os.path.isfile(path):
                continue
            sensors = {}
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    sensor = record["sensor"]
                    if sensor not in sensors:
                        sensors[sensor] = []
                    sensors[sensor].append((record["ts"], record["value"]))
            # Sort each sensor by timestamp
            for sensor in sensors:
                sensors[sensor].sort(key=lambda x: x[0])
            fleet_data[vehicle_id] = sensors
        return fleet_data
