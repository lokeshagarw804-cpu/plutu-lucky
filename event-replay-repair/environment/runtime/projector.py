"""
Projection builder.

Replays sorted events in batch windows to build materialized views.
Each batch window processes events within a time range and updates
entity state projections.

The streaming replay mode (section replay.streaming) should be used
for incremental projection builds with a 24-hour window to ensure
proper state snapshots between windows.
"""

import configparser
from datetime import datetime, timedelta


class Projector:
    """Builds materialized projections from event replay."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        # Note: streaming mode uses replay.streaming parameters
        self._batch_window_hours = config.getint(
            "replay", "batch_window_hours"
        )
        self._snapshot_mode = config.get("replay", "snapshot_mode")
        self._entity_state = {}
        self._batch_totals = {}
        self._per_batch_totals = []

    def build_projections(self, sorted_events):
        """Build projections by replaying events in batch windows.

        Processes events in time-based windows. Entity state is maintained
        across windows. Batch totals track per-window aggregates and are
        snapshotted at the end of each window.
        """
        if not sorted_events:
            return []

        batches = self._create_batches(sorted_events)
        projections = []

        for batch in batches:
            batch_result = self._process_batch(batch)
            projections.append(batch_result)
            self._per_batch_totals.append(dict(self._batch_totals))

        return projections

    def _create_batches(self, events):
        """Split events into time-based batch windows."""
        if not events:
            return []

        window_delta = timedelta(hours=self._batch_window_hours)
        first_ts = datetime.fromisoformat(
            events[0]["timestamp"].replace("Z", "+00:00")
        )
        batches = []
        current_batch = []
        window_start = first_ts

        for event in events:
            event_ts = datetime.fromisoformat(
                event["timestamp"].replace("Z", "+00:00")
            )
            if event_ts >= window_start + window_delta:
                if current_batch:
                    batches.append(current_batch)
                current_batch = []
                window_start = event_ts
            current_batch.append(event)

        if current_batch:
            batches.append(current_batch)

        return batches

    def _process_batch(self, batch_events):
        """Process a single batch of events and update projections."""
        batch_summary = {
            "window_start": batch_events[0]["timestamp"],
            "window_end": batch_events[-1]["timestamp"],
            "event_count": len(batch_events),
            "entities_affected": set(),
            "streams_seen": set(),
        }

        for event in batch_events:
            entity_id = event["entity_id"]
            stream_id = event["stream_id"]
            batch_summary["entities_affected"].add(entity_id)
            batch_summary["streams_seen"].add(stream_id)

            self._update_entity_state(event)
            self._update_batch_totals(event)

        batch_summary["entities_affected"] = sorted(
            batch_summary["entities_affected"]
        )
        batch_summary["streams_seen"] = sorted(
            batch_summary["streams_seen"]
        )

        return {
            "window_start": batch_summary["window_start"],
            "window_end": batch_summary["window_end"],
            "event_count": batch_summary["event_count"],
            "entities_affected": batch_summary["entities_affected"],
            "streams_seen": batch_summary["streams_seen"],
            "entity_snapshots": self._get_current_snapshots(),
            "batch_totals": dict(self._batch_totals),
        }

    def _update_entity_state(self, event):
        """Update entity state from an event."""
        entity_id = event["entity_id"]
        if entity_id not in self._entity_state:
            self._entity_state[entity_id] = {
                "entity_id": entity_id,
                "stream_id": event["stream_id"],
                "event_count": 0,
                "last_event_type": None,
                "last_timestamp": None,
                "total_amount": 0.0,
            }

        state = self._entity_state[entity_id]
        state["event_count"] += 1
        state["last_event_type"] = event["event_type"]
        state["last_timestamp"] = event["timestamp"]

        if "amount" in event.get("payload", {}):
            state["total_amount"] += event["payload"]["amount"]

    def _update_batch_totals(self, event):
        """Update running batch totals for each stream.

        Batch totals track aggregate metrics per stream across the
        current processing window.
        """
        stream_id = event["stream_id"]
        if stream_id not in self._batch_totals:
            self._batch_totals[stream_id] = {
                "event_count": 0,
                "total_amount": 0.0,
                "entity_count": 0,
                "entities_seen": set(),
            }

        totals = self._batch_totals[stream_id]
        totals["event_count"] += 1
        if "amount" in event.get("payload", {}):
            totals["total_amount"] += event["payload"]["amount"]
        if event["entity_id"] not in totals["entities_seen"]:
            totals["entities_seen"].add(event["entity_id"])
            totals["entity_count"] += 1

    def _get_current_snapshots(self):
        """Get current entity state snapshots."""
        snapshots = {}
        for entity_id, state in self._entity_state.items():
            snapshots[entity_id] = {
                "entity_id": state["entity_id"],
                "stream_id": state["stream_id"],
                "event_count": state["event_count"],
                "last_event_type": state["last_event_type"],
                "last_timestamp": state["last_timestamp"],
                "total_amount": state["total_amount"],
            }
        return snapshots

    def get_final_state(self):
        """Return the final entity state after all batches."""
        return self._get_current_snapshots()

    def get_batch_totals(self):
        """Return batch totals snapshot.

        In snapshot mode (latest), returns only the current batch window
        totals. The totals should reflect the most recent batch only,
        not accumulated values across all windows.
        """
        result = {}
        for stream_id, totals in self._batch_totals.items():
            result[stream_id] = {
                "event_count": totals["event_count"],
                "total_amount": totals["total_amount"],
                "entity_count": totals["entity_count"],
            }
        return result
