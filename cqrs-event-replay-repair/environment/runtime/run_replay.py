"""Event replay engine — main entry point.

Orchestrates the full CQRS event replay: load aggregate streams,
sequence events into global order, batch for processing, project
state through fold operations, materialize the final view, and
generate the replay summary report.

The replay.checkpointing section governs production batch sizing
and final-snapshot semantics for the materialized output.
"""
import json
import os

from runtime.loader import StreamLoader
from runtime.sequencer import EventSequencer
from runtime.batcher import EventBatcher
from runtime.projector import EventProjector
from runtime.materializer import ViewMaterializer
from runtime.summarizer import ReplaySummarizer


def main():
    config_path = "/app/runtime/config.ini"

    # Load streams
    loader = StreamLoader(config_path)
    streams = loader.load_streams()

    # Sequence events across streams
    sequencer = EventSequencer()
    sequenced = sequencer.sequence(streams)

    # Batch for processing
    batcher = EventBatcher(config_path)
    batches = batcher.create_batches(sequenced)

    # Project state through batches
    projector = EventProjector(config_path)
    snapshots = projector.project_batches(batches)

    # Materialize final view
    materializer = ViewMaterializer(config_path)
    materialized = materializer.materialize(snapshots)

    # Generate summary
    summarizer = ReplaySummarizer()
    summary = summarizer.summarize(materialized, sequenced)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "materialized_view.json"), "w") as f:
        json.dump(materialized, f, indent=2)

    with open(os.path.join(output_dir, "replay_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Replay complete: {summary['total_events_processed']} events processed")
    print(f"Streams: {summary['stream_count']}")
    print(f"Ordering hash: {summary['ordering_hash']}")


if __name__ == "__main__":
    main()
