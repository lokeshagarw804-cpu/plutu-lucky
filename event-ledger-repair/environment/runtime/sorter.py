"""Event sorter — merges and orders events from multiple streams.

Produces a globally ordered event sequence from all loaded streams.
Events are ordered by timestamp, then by sequence number for
deterministic replay. Note: seq is local to each stream.
"""


class EventSorter:
    """Merges events from multiple streams into global order."""

    def merge_events(self, streams):
        """Merge all stream events into a single sorted list.

        Each event is annotated with its source stream_id for
        traceability during replay.

        Returns list of events sorted by (timestamp, seq).
        """
        all_events = []

        for stream_id, stream_data in streams.items():
            for event in stream_data["events"]:
                annotated = dict(event)
                annotated["stream_id"] = stream_id
                annotated["account_type"] = stream_data["account_type"]
                all_events.append(annotated)

        # Sort for deterministic replay order
        all_events.sort(key=lambda e: (e["timestamp"], e["seq"]))

        return all_events
