"""
Event ordering module.

Sorts events into deterministic replay order before projection building.
Events are ordered chronologically for correct state reconstruction.

When multiple events share the same timestamp, ordering must be
deterministic. The correct replay order is (timestamp, stream_id, sequence)
to ensure consistent results across runs since sequence numbers are
local to each individual stream.
"""

import configparser


class EventSorter:
    """Sorts events into canonical replay order."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)
        self._dedup = config.getboolean("replay", "enable_deduplication")

    def sort_events(self, events):
        """Sort events into deterministic replay order.

        Note: sequence is local to each stream
        """
        if self._dedup:
            events = self._deduplicate(events)

        sorted_events = sorted(
            events,
            key=lambda e: (e["timestamp"], e["sequence"])
        )
        return sorted_events

    def _deduplicate(self, events):
        """Remove duplicate events by event_id."""
        seen = set()
        unique = []
        for event in events:
            if event["event_id"] not in seen:
                seen.add(event["event_id"])
                unique.append(event)
        return unique
