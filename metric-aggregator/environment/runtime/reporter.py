"""Health reporter — generates the final health assessment report.

Combines ranking data and detected incidents into a structured JSON
report containing per-node health summaries and overall system health.
"""


class HealthReporter:
    """Generates structured health assessment reports."""

    def generate_report(self, ranked, incidents):
        """Build the health assessment report.

        Args:
            ranked: dict of node_id -> list of {window_idx, raw_score, percentile_rank}
            incidents: list of incident dicts

        Returns:
            dict with summary and node_details sections
        """
        # Build per-node summary
        node_details = []
        for node_id, windows in ranked.items():
            if not windows:
                continue

            scores = [w["percentile_rank"] for w in windows]
            raw_scores = [w["raw_score"] for w in windows]

            node_incidents = [inc for inc in incidents if inc["node_id"] == node_id]

            detail = {
                "node_id": node_id,
                "avg_percentile": round(sum(scores) / len(scores), 4),
                "max_percentile": max(scores),
                "avg_raw_score": round(sum(raw_scores) / len(raw_scores), 4),
                "total_incidents": len(node_incidents),
                "total_degraded_windows": sum(
                    inc["duration_windows"] for inc in node_incidents
                ),
            }
            node_details.append(detail)

        # Sort by avg_percentile descending (worst first)
        node_details.sort(key=lambda x: x["avg_percentile"], reverse=True)

        # Build summary
        total_incidents = len(incidents)
        nodes_affected = len(set(inc["node_id"] for inc in incidents))
        max_severity = max(
            (inc["severity"] for inc in incidents), default=0.0
        )
        total_degraded_windows = sum(
            inc["duration_windows"] for inc in incidents
        )

        summary = {
            "total_incidents": total_incidents,
            "nodes_affected": nodes_affected,
            "max_severity": max_severity,
            "total_degraded_windows": total_degraded_windows,
            "worst_node": node_details[0]["node_id"] if node_details else None,
        }

        return {
            "summary": summary,
            "node_details": node_details,
            "incidents": incidents,
        }
