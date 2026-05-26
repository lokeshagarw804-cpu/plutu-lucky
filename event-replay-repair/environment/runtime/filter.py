"""
Event type filter.

Filters events based on the configured allowed event types from
the streams section. Only events matching registered types proceed
to the replay engine for projection building.
"""

import configparser


class EventFilter:
    """Filters events against the configured type whitelist."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        raw_types = config.get("streams", "event_types")
        self._allowed_types = set(raw_types.split(","))

    def filter_events(self, events):
        """Return only events whose type is in the allowed set."""
        accepted = []
        for event in events:
            if event["event_type"] in self._allowed_types:
                accepted.append(event)
        return accepted
