"""Partition merger — aggregates per-partition statistics snapshots.

When the index is scanned in partitions (windows), each partition
produces a category distribution snapshot. This module merges those
snapshots into the final reported statistics.
"""


class PartitionMerger:
    """Merges partition-level statistics into final aggregates."""

    def __init__(self):
        self._merged = {}

    def add_partition_snapshot(self, partition_counts):
        """Aggregate a partition's category counts into the merged result.

        Each partition provides a complete snapshot of category distribution
        for that window of the index.
        """
        for category, count in partition_counts.items():
            self._merged[category] = self._merged.get(category, 0) + count

    def get_merged_counts(self):
        """Return the final merged category counts."""
        return dict(self._merged)

    def reset(self):
        """Clear merged state for reuse."""
        self._merged = {}
