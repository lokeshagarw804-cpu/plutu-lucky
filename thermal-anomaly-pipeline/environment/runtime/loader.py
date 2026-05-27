"""
Sensor data loader for thermal monitoring zones.
Reads JSON fixture files and returns normalized reading streams.
"""
import json
import os
from typing import List, Dict, Any


def load_zone_data(data_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load all zone sensor data from JSON files in the given directory.
    Returns a dict mapping zone_id -> list of readings sorted by timestamp.
    """
    zones = {}
    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith('.json'):
            continue
        filepath = os.path.join(data_dir, filename)
        with open(filepath, 'r') as f:
            data = json.load(f)
        zone_id = data['zone_id']
        readings = sorted(data['readings'], key=lambda r: r['timestamp'])
        zones[zone_id] = readings
    return zones


def get_zone_metadata(data_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract metadata (thresholds, weights) for each zone.
    """
    metadata = {}
    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith('.json'):
            continue
        filepath = os.path.join(data_dir, filename)
        with open(filepath, 'r') as f:
            data = json.load(f)
        zone_id = data['zone_id']
        metadata[zone_id] = {
            'threshold_high': data.get('threshold_high', 85.0),
            'threshold_critical': data.get('threshold_critical', 95.0),
            'weight_factors': data.get('weight_factors', [1.0]),
            'window_size': data.get('window_size', 5),
            'zone_name': data.get('zone_name', zone_id),
        }
    return metadata
