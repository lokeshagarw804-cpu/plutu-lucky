"""Deduplicator — removes duplicate events within a dedup window.

Checks for events with the same event_id that appear within a
configurable window of positions. If duplicates are found, only
the first occurrence is kept. The dedup window size determines
how many preceding events to check against.

Window count should be: ceil(event_count / dedup_window).
"""
import configparser
import math


class EventDeduplicator:
    """Removes duplicate events within configured window."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window = self._config.getint("projection", "dedup_window")

    def deduplicate(self, replay_sequence):
        """Remove duplicate events within dedup window.

        Scans the replay sequence and removes any event whose event_id
        was already seen within the preceding window positions.
        Returns deduplicated sequence and dedup stats.
        """
        seen_windows = []
        deduplicated = []
        removed = []

        for event in replay_sequence:
            eid = event["event_id"]
            # Check within the window
            window_start = max(0, len(seen_windows) - (self._window + 1))
            recent_ids = seen_windows[window_start:]

            if eid in recent_ids:
                removed.append(event)
            else:
                deduplicated.append(event)
            seen_windows.append(eid)

        return deduplicated, {
            "total_input": len(replay_sequence),
            "total_output": len(deduplicated),
            "duplicates_removed": len(removed),
            "window_size": self._window,
        }

    def get_window_size(self):
        """Return configured dedup window size."""
        return self._window
