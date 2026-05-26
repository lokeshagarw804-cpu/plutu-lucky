"""Log loader — reads and merges event logs from service nodes.

Loads JSONL event files from each node, parses timestamps,
and groups events that fall within the configured merge window
for synchronized causality analysis.
"""
import configparser
import json
import os


class LogLoader:
    """Loads and merges distributed event logs by time window."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._log_dir = self._config.get("sources", "log_dir")
        self._window_ms = self._config.getint("merge", "window_ms")

    def load_and_merge(self):
        """Load all node logs and merge events within time windows."""
        all_events = []
        log_files = sorted(
            f for f in os.listdir(self._log_dir) if f.endswith(".jsonl")
        )
        for fname in log_files:
            node_id = fname.replace(".jsonl", "")
            path = os.path.join(self._log_dir, fname)
            with open(path, "r") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    event = json.loads(line)
                    event["node_id"] = node_id
                    all_events.append(event)

        # Sort by timestamp for merging
        all_events.sort(key=lambda e: (e["ts_ms"], e["node_id"], e["seq"]))

        # Group into merge windows
        merged = self._apply_windows(all_events)
        return merged

    def _apply_windows(self, sorted_events):
        """Group events within window_ms of the group start.

        Events whose timestamp falls within window_ms of the first
        event in the current group belong to the same window.
        """
        if not sorted_events:
            return []

        groups = []
        current_group = [sorted_events[0]]
        group_start = sorted_events[0]["ts_ms"]

        for event in sorted_events[1:]:
            if event["ts_ms"] - group_start < self._window_ms:
                current_group.append(event)
            else:
                groups.append(current_group)
                current_group = [event]
                group_start = event["ts_ms"]

        if current_group:
            groups.append(current_group)

        # Annotate events with their window index
        result = []
        for idx, group in enumerate(groups):
            for event in group:
                event["window"] = idx
            result.extend(group)
        return result
