"""Projector — applies events to build materialized read-model views.

Processes the ordered event sequence and builds projection state.
Takes snapshots at the configured interval from the projection.materialized
section. Each snapshot captures the current state of the projection.

Snapshots should reflect only the events processed in that interval —
they should not accumulate state from previous intervals.
"""
import configparser


class Projector:
    """Builds materialized view projections from event sequence."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        # Snapshot interval controls how often state is captured
        self._snapshot_interval = self._config.getint(
            "projection", "snapshot_interval"
        )

    def project(self, replay_sequence):
        """Apply events and produce snapshots at configured intervals.

        Processes events in order, building projection state. Every
        snapshot_interval events, a snapshot of the current interval
        state is captured.

        Returns list of snapshot dicts and final projection state.
        """
        snapshots = []
        # Running counters for projection
        running_counts = {}
        interval_start = 0

        for idx, event in enumerate(replay_sequence):
            agg_id = event["aggregate_id"]
            running_counts[agg_id] = running_counts.get(agg_id, 0) + 1

            # Take snapshot at interval boundary
            if (idx + 1) % self._snapshot_interval == 0:
                snapshots.append({
                    "snapshot_id": len(snapshots),
                    "events_processed": idx + 1,
                    "interval_start": interval_start,
                    "interval_end": idx,
                    "state": dict(running_counts),
                })
                interval_start = idx + 1

        # Final snapshot for remaining events
        if interval_start <= len(replay_sequence) - 1:
            snapshots.append({
                "snapshot_id": len(snapshots),
                "events_processed": len(replay_sequence),
                "interval_start": interval_start,
                "interval_end": len(replay_sequence) - 1,
                "state": dict(running_counts),
            })

        return snapshots, running_counts

    def get_snapshot_interval(self):
        """Return configured snapshot interval."""
        return self._snapshot_interval
