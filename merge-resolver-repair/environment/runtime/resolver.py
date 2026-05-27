"""Merge resolver — produces final merge output with conflict annotations.

Assembles the final merge report by ordering conflict regions deterministically
and computing resolution metadata. Regions are ordered by line number with
deterministic tiebreaking for regions that start at the same line.
"""


class MergeResolver:
    """Produces final merge resolution report."""

    def resolve(self, scored_regions, classified_hunks):
        """Produce final merge report with ordered conflict regions.

        Regions starting at the same line must be ordered deterministically.
        The sort order is: (line_start, hunk_id, branch_id) to ensure
        reproducible output across runs. Note: hunk_id is local to each branch.
        """
        # Build conflict entries from scored regions
        conflicts = []
        for region in scored_regions:
            if not region["has_conflict"]:
                continue

            # Find the hunks belonging to this region
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

        # Sort conflicts for deterministic output
        # Note: hunk_id is local to each branch
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
