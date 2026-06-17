"""Event sequencer — merges and orders events from multiple streams.

Combines events from all loaded aggregate streams into a single ordered
sequence for replay. The ordering must be fully deterministic to ensure
consistent materialized views across replays.
"""


class EventSequencer:
    """Merges multiple event streams into a single ordered sequence."""

    def sequence(self, streams):
        """Merge all stream events into a global ordered sequence.

        Each event is tagged with its source stream_id for provenance.
        The sort produces a deterministic total order suitable for replay.
        """
        merged = []
        for stream_id, stream_data in streams.items():
            for event in stream_data["events"]:
                merged.append({
                    "stream_id": stream_id,
                    "seq": event["seq"],
                    "timestamp": event["timestamp"],
                    "type": event["type"],
                    "payload": event["payload"],
                })

        # Sort for deterministic replay ordering
        merged.sort(key=lambda e: (e["timestamp"], e["seq"]))
        return merged
