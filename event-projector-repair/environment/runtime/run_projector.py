"""Event projector — main entry point.

Orchestrates the full event sourcing projection: load aggregate
streams, build replay sequence, deduplicate, project into
materialized views, and produce the final read-model output.
"""
import json
import os

from runtime.loader import AggregateLoader
from runtime.replayer import EventReplayer
from runtime.deduplicator import EventDeduplicator
from runtime.projector import Projector
from runtime.view_builder import ViewBuilder


def main():
    config_path = "/app/runtime/config.ini"

    # Load aggregate event streams
    loader = AggregateLoader(config_path)
    aggregates = loader.load_aggregates()

    # Build replay sequence (merged chronological order)
    replayer = EventReplayer()
    replay_sequence = replayer.build_replay_sequence(aggregates)

    # Deduplicate events
    deduplicator = EventDeduplicator(config_path)
    deduped_sequence, dedup_stats = deduplicator.deduplicate(replay_sequence)

    # Project into materialized views
    projector = Projector(config_path)
    snapshots, final_state = projector.project(deduped_sequence)

    # Build final view
    builder = ViewBuilder()
    view = builder.build_view(snapshots, final_state, dedup_stats, aggregates)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    # Materialized view
    with open(os.path.join(output_dir, "materialized_view.json"), "w") as f:
        json.dump(view, f, indent=2)

    # Replay sequence (for ordering verification)
    replay_output = {
        "total_events": len(deduped_sequence),
        "replay_order": [
            {
                "event_id": e["event_id"],
                "aggregate_id": e["aggregate_id"],
                "timestamp": e["timestamp"],
                "seq": e["seq"],
            }
            for e in deduped_sequence
        ],
        "snapshot_interval": projector.get_snapshot_interval(),
    }
    with open(os.path.join(output_dir, "replay_sequence.json"), "w") as f:
        json.dump(replay_output, f, indent=2)


if __name__ == "__main__":
    main()
