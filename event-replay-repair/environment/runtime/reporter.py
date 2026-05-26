"""
Report generator for event replay.

Produces structured output files from the replay results including
the event processing log and final replay summary.

The event log entries must be in deterministic order matching the
replay sequence. For events with the same timestamp from different
streams, ordering is by (timestamp, stream_id, sequence) to ensure
reproducible results.
"""

import json
import os
import configparser


class ReplayReporter:
    """Generates output reports from replay results."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._event_log_path = config.get("projections", "event_log_path")
        self._summary_path = config.get("output", "summary_path")
        self._include_metadata = config.getboolean(
            "projections", "include_metadata"
        )

    def generate_reports(self, sorted_events, projections, final_state,
                         batch_totals):
        """Generate all output reports."""
        event_log = self._build_event_log(sorted_events)
        summary = self._build_summary(
            sorted_events, projections, final_state, batch_totals
        )

        self._write_json(self._event_log_path, event_log)
        self._write_json(self._summary_path, summary)

        return event_log, summary

    def _build_event_log(self, sorted_events):
        """Build the processed event log."""
        entries = []
        for i, event in enumerate(sorted_events):
            entry = {
                "position": i,
                "event_id": event["event_id"],
                "stream_id": event["stream_id"],
                "sequence": event["sequence"],
                "timestamp": event["timestamp"],
                "event_type": event["event_type"],
                "entity_id": event["entity_id"],
            }
            if self._include_metadata:
                entry["payload_keys"] = sorted(
                    event.get("payload", {}).keys()
                )
            entries.append(entry)

        return {
            "total_events": len(entries),
            "entries": entries,
        }

    def _build_summary(self, sorted_events, projections, final_state,
                       batch_totals):
        """Build the replay summary report."""
        stream_counts = {}
        type_counts = {}
        for event in sorted_events:
            sid = event["stream_id"]
            etype = event["event_type"]
            stream_counts[sid] = stream_counts.get(sid, 0) + 1
            type_counts[etype] = type_counts.get(etype, 0) + 1

        return {
            "total_events_processed": len(sorted_events),
            "total_batches": len(projections),
            "stream_counts": stream_counts,
            "type_counts": type_counts,
            "total_entities": len(final_state),
            "entity_states": final_state,
            "batch_totals": batch_totals,
        }

    def _write_json(self, path, data):
        """Write data as formatted JSON."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
