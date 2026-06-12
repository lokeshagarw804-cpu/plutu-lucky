"""Fleet data loader — reads and merges GPS telemetry from vehicle feeds.

Loads JSONL fleet files, parses timestamps into epoch seconds, and
groups readings from different feeds that fall within the configured
time window for synchronized processing.
"""
import configparser
import json
import os
from datetime import datetime, timezone


class FleetLoader:
    """Loads fleet telemetry and merges readings by time window."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("fleet", "source_dir")
        self._window = self._config.getint("timing", "window_seconds")

    def load_and_merge(self):
        """Load all fleet feeds and merge readings within time windows."""
        all_readings = []
        feed_files = sorted(
            f for f in os.listdir(self._source_dir) if f.endswith(".jsonl")
        )
        for fname in feed_files:
            fleet_id = fname.replace(".jsonl", "")
            path = os.path.join(self._source_dir, fname)
            with open(path, "r") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    record["fleet_id"] = fleet_id
                    record["epoch"] = self._parse_timestamp(record["timestamp"])
                    all_readings.append(record)

        # Sort by epoch for merging
        all_readings.sort(key=lambda r: (r["epoch"], r["fleet_id"], r["seq"]))

        # Group readings within time windows
        merged = self._merge_windows(all_readings)
        return merged

    def _parse_timestamp(self, ts_str):
        """Convert ISO timestamp to epoch seconds."""
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return int(dt.timestamp())

    def _merge_windows(self, sorted_readings):
        """Group readings that fall within window_seconds of the group start.

        A new group begins when a reading's epoch exceeds the current group
        start epoch by more than the window threshold.
        """
        if not sorted_readings:
            return []

        groups = []
        current_group = [sorted_readings[0]]
        group_start = sorted_readings[0]["epoch"]

        for reading in sorted_readings[1:]:
            # Check if reading falls within the time window
            if reading["epoch"] - group_start <= self._window:
                current_group.append(reading)
            else:
                groups.append(current_group)
                current_group = [reading]
                group_start = reading["epoch"]

        if current_group:
            groups.append(current_group)

        # Flatten but preserve group boundaries as metadata
        result = []
        for group_idx, group in enumerate(groups):
            for reading in group:
                reading["window_group"] = group_idx
            result.extend(group)
        return result
