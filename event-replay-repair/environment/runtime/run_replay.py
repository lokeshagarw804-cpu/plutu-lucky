"""Event replay engine — main entry point.

Orchestrates the full CQRS event replay: loads command streams,
sequences events into global order, projects materialized state,
builds periodic snapshots, and reconciles for audit verification.
"""
import json
import os

from runtime.stream_loader import StreamLoader
from runtime.sequencer import EventSequencer
from runtime.projector import EventProjector
from runtime.snapshot_builder import SnapshotBuilder
from runtime.reconciler import Reconciler


def main():
    config_path = "/app/runtime/config.ini"

    # Load command streams
    loader = StreamLoader(config_path)
    streams = loader.load_streams()

    # Sequence events across streams
    sequencer = EventSequencer(config_path)
    sequenced = sequencer.sequence_events(streams)

    # Project materialized state
    projector = EventProjector(config_path)
    final_balances = projector.project(sequenced)

    # Build snapshots
    snapshot_builder = SnapshotBuilder(config_path)
    snapshots = snapshot_builder.build_snapshots(sequenced)

    # Reconcile
    reconciler = Reconciler(config_path)
    report = reconciler.reconcile(final_balances, snapshots)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    projection_output = {
        "total_events_processed": len(sequenced),
        "total_accounts": len(final_balances),
        "balances": {k: v for k, v in sorted(final_balances.items())},
        "streams_loaded": sorted(streams.keys()),
    }
    with open(os.path.join(output_dir, "projection_state.json"), "w") as f:
        json.dump(projection_output, f, indent=2)

    snapshot_output = {
        "interval_events": 10,
        "total_snapshots": len(snapshots),
        "snapshots": snapshots,
    }
    with open(os.path.join(output_dir, "snapshots.json"), "w") as f:
        json.dump(snapshot_output, f, indent=2)

    with open(os.path.join(output_dir, "reconciliation.json"), "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
