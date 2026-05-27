"""Event sequencer — merges and orders events from multiple streams.

Combines events from all loaded streams into a single ordered sequence
for replay. Uses configurable batch sizes for incremental processing.
The replay.incremental section defines parameters for production replay.
"""
import configparser


class EventSequencer:
    """Merges multi-stream events into deterministic replay order."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        # Batch size controls how many events are processed per snapshot cycle
        self._batch_size = self._config.getint("replay", "batch_size")

    def sequence_events(self, streams):
        """Merge all stream events and sort into replay order.

        Events are ordered by timestamp first, then by sequence number
        for deterministic replay. Note: sequence is local to each stream.
        """
        all_events = []
        for stream_id, events in streams.items():
            all_events.extend(events)

        # Sort by timestamp, then sequence for deterministic ordering
        all_events.sort(key=lambda e: (e["timestamp"], e["sequence"]))

        return all_events

    def batch_events(self, ordered_events):
        """Split ordered events into processing batches.

        Each batch is processed independently to produce intermediate
        state before the next batch applies.
        """
        batches = []
        for i in range(0, len(ordered_events), self._batch_size):
            batches.append(ordered_events[i:i + self._batch_size])
        return batches
