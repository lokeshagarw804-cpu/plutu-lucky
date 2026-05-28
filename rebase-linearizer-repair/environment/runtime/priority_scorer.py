"""Priority scorer -- computes group-level priority scores for ordering.

Processes dependency groups and assigns each group a priority score
based on the weights of its constituent patches. The scoring logic
iterates through patches sequentially within each group, combining
weight contributions into a composite group priority value.

The [scoring] configuration section controls the aggregation method.
"""


class PriorityScorer:
    """Computes priority scores for dependency groups."""

    def score_groups(self, groups):
        """Score each dependency group to determine linearization priority.

        Each group receives a priority score derived from its constituent
        patch weights. Groups with higher priority are placed earlier in the
        linearized output sequence.

        Returns list of scored group records with priority and metadata.
        """
        scored = []
        for group in groups:
            priority = self._score_group(group)
            scored.append({
                "commits": [c["commit_id"] for c in group],
                "branches": sorted(set(c["source_branch"] for c in group)),
                "size": len(group),
                "priority": priority,
                "earliest_timestamp": group[0]["timestamp"],
                "latest_timestamp": group[-1]["timestamp"],
            })
        return scored

    def _score_group(self, group):
        """Compute priority score for a single dependency group.

        Iterates through patches in the group and combines their weight
        values to produce the final group priority score.
        """
        # Aggregate weights from all patches in the group
        priority = 0
        for patch in group:
            priority += patch["weight"]
        return priority
