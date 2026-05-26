"""
Sensor data loader.

Reads readings from station JSON files in /app/runtime/data/.
Each station file contains timestamped sensor readings across
multiple measurement channels.
"""

import json
import os


def load_readings(data_dir="/app/runtime/data"):
    """Load all sensor readings from station data files.

    Returns a list of reading dicts from all stations.
    """
    readings = []
    for filename in sorted(os.listdir(data_dir)):
        if filename.startswith("station_") and filename.endswith(".json"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r") as f:
                records = json.load(f)
                readings.extend(records)
    return readings
