"""Pipeline data loader — reads segment sensor readings from JSON files.

Loads time-series pressure readings for each active pipeline segment.
Each segment contains multiple sensors with synchronized sampling.
"""
import configparser
import json
import os


class PipelineLoader:
    """Loads raw pressure sensor data from segment JSON files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("pipeline", "source_dir")
        raw_segments = self._config.get("segments", "active_segments")
        self._active = [s.strip() for s in raw_segments.split(",")]

    def load_segments(self):
        """Load pressure data for all active pipeline segments.

        Returns dict mapping segment_id to segment data including
        readings, sensor_ids, timing information.
        """
        segments = {}
        for seg_id in self._active:
            path = os.path.join(self._source_dir, f"{seg_id}.json")
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                data = json.load(f)
            segments[seg_id] = {
                "segment_id": seg_id,
                "sensor_ids": data["sensor_ids"],
                "sensor_count": data["sensor_count"],
                "sample_interval": data["sample_interval"],
                "start_time": data["start_time"],
                "readings": data["readings"],
            }
        return segments
