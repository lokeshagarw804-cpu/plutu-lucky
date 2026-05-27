"""Event sequencer — merges and orders events from multiple streams.

Combines events from all loaded aggregate streams into a single ordered
sequence for replay. Events are sorted by timestamp and sequence number
to produce a deterministic total order across streams.
"""


class EventSequencer:
    """Merges multiple event streams into a single ordered sequence."""

    def sequence(self, streams):
        """Merge all stream events into a global ordered sequence.

        Each event is tagged with its source stream_id for provenance.
        Events are ordered by timestamp then sequence number for
        deterministic replay. Note: seq is local to each stream.
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
