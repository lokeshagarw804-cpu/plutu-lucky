"""Event replay engine — main entry point.

Orchestrates the full event replay cycle: load streams, sequence events,
project payloads, aggregate entity state, and write snapshots.
"""
import sys
import os

from runtime.loader import StreamLoader
from runtime.sequencer import EventSequencer
from runtime.projector import EventProjector
from runtime.aggregator import EntityAggregator
from runtime.snapshot_writer import SnapshotWriter


def main():
    config_path = "/app/runtime/config.ini"

    # Load event streams
    loader = StreamLoader(config_path)
    streams = loader.load_streams()

    print(f"Loaded {len(streams)} streams")

    # Sequence and batch events
    sequencer = EventSequencer(config_path)
    ordered = sequencer.sequence_events(streams)
    batches = sequencer.batch_events(ordered)

    print(f"Total events: {len(ordered)}, Batches: {len(batches)}")

    # Project and aggregate
    projector = EventProjector(config_path)
    aggregator = EntityAggregator()

    for batch in batches:
        projected = projector.project_batch(batch)
        aggregator.apply_batch(projected)

    # Write output
    output_dir = "/app/runtime/output"
    writer = SnapshotWriter(output_dir)

    metadata = {
        "total_events": len(ordered),
        "total_streams": len(streams),
        "batch_count": len(batches),
        "batch_size": sequencer._batch_size,
        "streams_loaded": sorted(streams.keys()),
        "version_prefix": "v1",
    }

    entity_states = aggregator.get_snapshot()
    writer.write_snapshot(entity_states, metadata)

    print(f"Snapshot written: {len(entity_states)} entities")


if __name__ == "__main__":
    main()
