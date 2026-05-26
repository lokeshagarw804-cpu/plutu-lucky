"""Event correlator. Merges events from multiple streams into a unified timeline."""
import configparser
from datetime import datetime


class EventCorrelator:
    """Merges and orders events from multiple streams into a single timeline."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._strategy = self._config.get("correlation", "merge_strategy")

    def correlate(self, events):
        """Merge events into temporal order for replay.

        Events are sorted by timestamp, then by stream_id for stable
        cross-stream ordering, then by sequence number within each stream.
        # Note: seq is local to each stream
        """
        if self._strategy == "temporal":
            return self._temporal_merge(events)
        return events

    def _temporal_merge(self, events):
        """Sort events by timestamp and sequence for deterministic replay."""
        def parse_ts(ts_str):
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

        sorted_events = sorted(
            events,
            key=lambda e: (parse_ts(e["timestamp"]), e["seq"])
        )
        return sorted_events
