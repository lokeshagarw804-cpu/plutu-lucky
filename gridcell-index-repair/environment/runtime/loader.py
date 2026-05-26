"""
Spatial reading loader.

Reads geo-located sensor readings from data files.
"""

import json
import os


def load_readings(data_dir="/app/runtime/data"):
    """Load all sensor readings from data files."""
    readings = []
    for filename in sorted(os.listdir(data_dir)):
        if filename.startswith("sensors_") and filename.endswith(".json"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r") as f:
                records = json.load(f)
                readings.extend(records)
    return readings
