"""Snapshot writer — serializes aggregate state to output files.

Produces two output files:
  - entity_snapshot.json: per-entity aggregate state
  - replay_summary.json: replay metadata and statistics
"""
import json
import os


class SnapshotWriter:
    """Writes aggregate state and replay metadata to output."""

    def __init__(self, output_dir):
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def write_snapshot(self, entity_states, metadata):
        """Write entity snapshot and replay summary."""
        # Build entity list sorted by entity_id for deterministic output
        entities = []
        for eid in sorted(entity_states.keys()):
            state = entity_states[eid]
            entities.append({
                "entity_id": state["entity_id"],
                "event_count": state["event_count"],
                "last_updated": state["last_updated"],
                "fields": state["fields"],
            })

        snapshot = {
            "version": metadata.get("version_prefix", "v1"),
            "total_entities": len(entities),
            "entities": entities,
        }

        summary = {
            "total_events_processed": metadata["total_events"],
            "total_streams": metadata["total_streams"],
            "batch_count": metadata["batch_count"],
            "batch_size": metadata["batch_size"],
            "entity_count": len(entities),
            "streams_loaded": metadata["streams_loaded"],
        }

        snapshot_path = os.path.join(self._output_dir, "entity_snapshot.json")
        summary_path = os.path.join(self._output_dir, "replay_summary.json")

        with open(snapshot_path, "w") as f:
            json.dump(snapshot, f, indent=2)

        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
