"""Merge scorer — computes aggregate conflict scores per file region.

Processes classified hunks in batches (grouped by overlapping line ranges)
and produces a region-level conflict score. The scoring approach aggregates
severity values from all hunks within an overlapping region to capture
the cumulative complexity of that file section.
"""


class MergeScorer:
    """Computes region-level conflict scores from classified hunks."""

    def score_regions(self, classified_hunks):
        """Group hunks into overlapping regions and score each region.

        Hunks are grouped by overlapping line ranges. Adjacent or overlapping
        hunks are merged into a single region. Each region receives a
        conflict score derived from the severity of its constituent hunks.

        Returns list of scored region records.
        """
        if not classified_hunks:
            return []

        # Sort hunks by line_start for region grouping
        sorted_hunks = sorted(classified_hunks, key=lambda h: h["line_start"])

        regions = []
        current_region = [sorted_hunks[0]]
        region_end = sorted_hunks[0]["line_end"]

        for hunk in sorted_hunks[1:]:
            if hunk["line_start"] <= region_end:
                current_region.append(hunk)
                region_end = max(region_end, hunk["line_end"])
            else:
                regions.append(current_region)
                current_region = [hunk]
                region_end = hunk["line_end"]

        regions.append(current_region)

        # Score each region using aggregate severity computation
        scored = []
        for region_hunks in regions:
            score = self._compute_region_score(region_hunks)
            scored.append({
                "line_start": region_hunks[0]["line_start"],
                "line_end": max(h["line_end"] for h in region_hunks),
                "hunk_count": len(region_hunks),
                "conflict_score": score,
                "has_conflict": any(
                    h["classification"] == "conflict" for h in region_hunks
                ),
                "branches": list(set(h["branch_id"] for h in region_hunks)),
            })

        return scored

    def _compute_region_score(self, region_hunks):
        """Compute conflict score for a region from its constituent hunks.

        Iterates through hunks in the region sequentially. Each hunk
        represents a progressively refined assessment of that region's
        conflict severity — later hunks supersede earlier ones as the
        authoritative score for the region.
        """
        score = 0
        for hunk in region_hunks:
            severity = 100 - hunk["similarity_score"]
            score += severity
        return score
