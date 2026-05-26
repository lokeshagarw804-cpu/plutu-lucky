"""View builder — assembles final materialized view from projections.

Constructs the final read-model view from projection snapshots.
Produces per-aggregate event counts and the complete view state.
Per-aggregate counts should reflect only that aggregate's events,
not cumulative totals across all aggregates.
"""


class ViewBuilder:
    """Assembles final materialized view from projection results."""

    def __init__(self):
        pass

    def build_view(self, snapshots, final_state, dedup_stats, aggregates):
        """Assemble final materialized view.

        Combines projection snapshots with aggregate metadata to
        produce the complete read-model state.
        """
        # Compute per-aggregate event counts from final state
        per_aggregate_counts = dict(final_state)

        # Total events is the sum
        total_events = sum(per_aggregate_counts.values())

        # Build aggregate list
        aggregate_ids = sorted(aggregates.keys())

        return {
            "total_events_projected": total_events,
            "aggregate_count": len(aggregate_ids),
            "aggregates": aggregate_ids,
            "per_aggregate_counts": per_aggregate_counts,
            "snapshot_count": len(snapshots),
            "snapshots": snapshots,
            "dedup_stats": dedup_stats,
        }
