"""Report builder — assembles query results into structured output.

Produces summary statistics and detailed result listings from the
spatial query execution. Reports include per-source breakdowns and
aggregate metrics.
"""


class ReportBuilder:
    """Builds structured output reports from query results."""

    def build_report(self, results, index_stats, sources_loaded):
        """Build comprehensive query report.

        Args:
            results: list of feature results from range query
            index_stats: dict of spatial index statistics
            sources_loaded: list of source_ids that were loaded

        Returns tuple of (summary_dict, results_list).
        """
        # Compute per-source counts
        source_counts = {}
        for r in results:
            sid = r["source_id"]
            if sid not in source_counts:
                source_counts[sid] = 0
            source_counts[sid] += 1

        summary = {
            "total_results": len(results),
            "sources_queried": sorted(sources_loaded),
            "source_count": len(sources_loaded),
            "results_per_source": source_counts,
            "index_cells": index_stats["total_cells"],
            "index_features": index_stats["total_features"],
            "max_distance_km": (
                round(max(r["distance_km"] for r in results), 4)
                if results else 0.0
            ),
            "min_distance_km": (
                round(min(r["distance_km"] for r in results), 4)
                if results else 0.0
            ),
        }

        return summary, results
