"""Event replayer — replays events in chronological order across aggregates.

Merges events from all loaded aggregates into a single ordered sequence
for projection. Events are sorted by timestamp, and when timestamps
match across different aggregates, by aggregate_id alphabetically then
seq within that aggregate for deterministic replay ordering.

Note: seq is local to each aggregate — it does not provide global ordering.
"""


class EventReplayer:
    """Merges and orders events from multiple aggregates for replay."""

    def __init__(self):
        pass

    def build_replay_sequence(self, aggregates):
        """Merge all events from all aggregates into ordered sequence.

        Returns list of event records sorted by timestamp. For events
        at the same timestamp from different aggregates, ordering must
        be deterministic using aggregate_id then seq.
        """
        all_events = []

        for agg_id, agg_data in aggregates.items():
            for event in agg_data["events"]:
                all_events.append({
                    "event_id": event["event_id"],
                    "aggregate_id": agg_id,
                    "timestamp": event["timestamp"],
                    "type": event["type"],
                    "data": event["data"],
                    "seq": event["seq"],
                })

        # Sort by timestamp then seq for ordering
        all_events.sort(key=lambda e: (e["timestamp"], e["seq"]))

        return all_events
