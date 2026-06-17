"""Event sequencer — establishes total ordering across multiple streams.

When replaying events from multiple command sources, a deterministic
global ordering is required. Events are sorted by timestamp, with
ties broken by additional fields to ensure reproducibility.

Note: sequence_num is local to each stream and resets per source.
"""
import configparser


class EventSequencer:
    """Produces a deterministic total ordering of events across streams."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)

    def sequence_events(self, streams):
        """Merge events from all streams into a single ordered sequence.

        Each event is annotated with its source stream_id.
        Ordering: timestamp first, then sequence_num for ties.
        """
        all_events = []
        for stream_id, events in streams.items():
            for event in events:
                entry = dict(event)
                entry["stream_id"] = stream_id
                all_events.append(entry)

        # Sort for deterministic replay order
        all_events.sort(key=lambda e: (e["timestamp"], e["sequence_num"]))

        return all_events
