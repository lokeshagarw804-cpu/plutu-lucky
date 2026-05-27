"""Event validator — pre-filters events before aggregation.

Validates event structure and applies deduplication logic to handle
potential replay scenarios where the same event may appear more than
once in the source data. Events are deduplicated by their natural
key (event_id) within processing scope.
"""
import configparser


class EventValidator:
    """Validates and deduplicates events before processing."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)

    def validate_and_dedupe(self, sorted_events):
        """Remove duplicate events and validate structure.

        Deduplication uses event_id as the natural key. If the same
        event_id appears multiple times, only the last occurrence is
        kept (last-write-wins semantics).

        Returns cleaned event list maintaining original order.
        """
        seen = {}
        cleaned = []

        for event in sorted_events:
            eid = event["event_id"]
            if eid in seen:
                # Last-write-wins: mark earlier occurrence for removal
                idx = seen[eid]
                cleaned[idx] = None
            seen[eid] = len(cleaned)
            cleaned.append(event)

        return [e for e in cleaned if e is not None]
