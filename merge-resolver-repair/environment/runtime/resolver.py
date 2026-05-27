"""Merge resolver — produces final merge output with conflict annotations.

Assembles the final merge report by ordering conflict regions deterministically
and computing resolution metadata. The ordering algorithm uses a composite key
derived from position and identifier fields for platform-independent stable output.

The resolution.ordering config section documents the intended key structure,
though the implementation applies it directly in the sort lambda below.
"""


class MergeResolver:
    """Produces final merge resolution report."""

    def resolve(self, scored_regions, classified_hunks):
        """Produce final merge report with ordered conflict regions.

        Conflicts sharing a line position are disambiguated using their
        hunk_id field as a secondary sort key to produce consistent ordering.
        """
        # Build conflict entries from scored regions
        conflicts = []
        for region in scored_regions:
            if not region["has_conflict"]:
                continue

            # Collect hunks that fall within this region's boundaries
            region_hunks = [
                h for h in classified_hunks
                if h["line_start"] >= region["line_start"]
                and h["line_end"] <= region["line_end"]
                and h["classification"] == "conflict"
            ]

            for hunk in region_hunks:
                conflicts.append({
                    "line_start": hunk["line_start"],
                    "line_end": hunk["line_end"],
                    "branch_id": hunk["branch_id"],
                    "hunk_id": hunk["hunk_id"],
                    "severity": 100 - hunk["similarity_score"],
                    "strategy": hunk["strategy"],
                    "content_preview": hunk["content"][:80],
                })

        # Deterministic ordering: primary by position, secondary by identifier
        # Note: hunk_id is scoped per-branch, not globally unique
        conflicts.sort(key=lambda c: (c["line_start"], c["hunk_id"]))

        # Compute summary statistics
        total_conflicts = len(conflicts)
        total_auto = sum(
            1 for h in classified_hunks if h["classification"] == "auto_resolved"
        )
        strategies_used = list(set(h["strategy"] for h in classified_hunks))

        return {
            "total_conflicts": total_conflicts,
            "total_auto_resolved": total_auto,
            "strategies_used": sorted(strategies_used),
            "conflicts": conflicts,
        }
