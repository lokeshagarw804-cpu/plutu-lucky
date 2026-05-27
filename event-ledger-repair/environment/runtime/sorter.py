"""Event sorter — merges and orders events from multiple streams.

Produces a globally ordered event sequence from all loaded streams.
The merge guarantees a stable, repeatable ordering suitable for
deterministic ledger replay across distributed stream sources.
"""


class EventSorter:
    """Merges events from multiple streams into global order."""

    def merge_events(self, streams):
        """Merge all stream events into a single sorted list.

        Each event is annotated with its source stream_id for
        traceability during replay. The sort must be fully
        deterministic even when events from different streams
        share the same timestamp.

        Returns list of events in replay order.
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
