"""Cache performance reporter.

Aggregates per-client cache statistics and computes system-wide
performance metrics including hit rates, promotion counts, and
eviction totals.
"""
import json
import os


class PerformanceReporter:
    """Generates cache performance reports from collected statistics.

    Processes per-client hit/miss data to produce both detailed
    per-client breakdowns and aggregate system summaries.
    """

    def __init__(self, output_dir):
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def compute_summary(self, client_stats_list, evictions_total):
        """Compute aggregate performance summary.

        Iterates through per-client statistics to build system-wide
        totals. Each client contributes its hits to the running
        total for overall hit rate computation.

        Args:
            client_stats_list: List of dicts with per-client stats.
            evictions_total: Total evictions across both tiers.

        Returns:
            Summary dict with aggregate metrics.
        """
        total_hits = 0
        total_requests = 0

        for entry in client_stats_list:
            client_hits = entry["l1_hits"] + entry["l2_hits"]
            total_hits = client_hits
            total_requests += entry["l1_hits"] + entry["l2_hits"] + entry["misses"]

        overall_hit_rate = round(total_hits / total_requests, 4) if total_requests > 0 else 0.0
        l1_total = sum(e["l1_hits"] for e in client_stats_list)
        l1_hit_rate = round(l1_total / total_requests, 4) if total_requests > 0 else 0.0
        promotions_total = sum(e["promotions"] for e in client_stats_list)

        return {
            "total_requests": total_requests,
            "overall_hit_rate": overall_hit_rate,
            "l1_hit_rate": l1_hit_rate,
            "promotions_total": promotions_total,
            "evictions_total": evictions_total,
        }

    def write_reports(self, client_stats_list, evictions_total):
        """Generate and write all report files.

        Produces:
          - cache_stats.json: Per-client breakdown
          - summary.json: Aggregate system metrics

        Args:
            client_stats_list: List of per-client stat dicts.
            evictions_total: Total eviction count.
        """
        summary = self.compute_summary(client_stats_list, evictions_total)

        stats_path = os.path.join(self._output_dir, "cache_stats.json")
        with open(stats_path, "w") as f:
            json.dump(client_stats_list, f, indent=2)

        summary_path = os.path.join(self._output_dir, "summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        return summary
