"""Segment loader — reads pipeline sensor data from JSON files."""
import configparser
import json
import os


class SegmentLoader:
    """Loads raw sensor data for pipeline segments."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("pipeline", "source_dir")
        raw_segments = self._config.get("segments", "active_segments")
        self._active = [s.strip() for s in raw_segments.split(",")]

    def load_segments(self):
        """Load sensor readings for all active pipeline segments."""
        segments = {}
        for seg_id in self._active:
            path = os.path.join(self._source_dir, f"{seg_id}.json")
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                data = json.load(f)
            segments[seg_id] = {
                "segment_id": seg_id,
                "length_m": data["length_m"],
                "diameter_m": data["diameter_m"],
                "flow_readings": data["flow_readings"],
                "pressure_in": data["pressure_in"],
                "pressure_out": data["pressure_out"],
                "timestamps": data["timestamps"],
            }
        return segments
