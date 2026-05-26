"""Sensor data ingestion from JSONL station files."""
import configparser
import json
import os
from typing import List, Dict, Any


class SensorIngest:
    """Loads raw sensor readings from station data files."""

    def __init__(self, config_path: str):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._data_dir = self._config.get("sources", "data_dir")

    def load_all(self) -> List[Dict[str, Any]]:
        """Load all station files and return combined readings."""
        all_readings = []
        station_files = sorted(
            f for f in os.listdir(self._data_dir) if f.endswith(".jsonl")
        )

        for fname in station_files:
            station_name = fname.replace(".jsonl", "").replace("station_", "")
            fpath = os.path.join(self._data_dir, fname)
            with open(fpath, "r") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    record["station"] = station_name
                    all_readings.append(record)

        all_readings.sort(key=lambda r: (r["station"], r["ts_ms"]))
        return all_readings
