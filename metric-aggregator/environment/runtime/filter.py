"""Metric filter — aligns time windows across nodes with different start times.

Nodes may begin recording at different epochs. This module computes the
shared time range and trims each node's metric arrays to the overlapping
region so that downstream aggregation uses temporally aligned data.
"""


class MetricFilter:
    """Aligns metric arrays to shared time range across nodes."""

    def filter_aligned(self, nodes):
        """Trim all node metric arrays to the shared time overlap.

        For nodes with different start_epoch, compute the latest start
        and earliest end, then slice each node's arrays to that range.

        Returns filtered nodes dict with trimmed metric arrays and
        updated metadata.
        """
        if not nodes:
            return {}

        # Find shared time range
        latest_start = max(n["start_epoch"] for n in nodes.values())
        earliest_end = min(
            n["start_epoch"] + n["interval_sec"] * len(n["metrics"]["latency_ms"])
            for n in nodes.values()
        )

        if earliest_end <= latest_start:
            return {}

        filtered = {}
        for node_id, node in nodes.items():
            interval = node["interval_sec"]
            start_offset = int((latest_start - node["start_epoch"]) / interval)
            end_offset = int((earliest_end - node["start_epoch"]) / interval)

            trimmed_metrics = {}
            for metric_name, values in node["metrics"].items():
                trimmed_metrics[metric_name] = values[start_offset:end_offset]

            filtered[node_id] = {
                "node_id": node_id,
                "region": node["region"],
                "start_epoch": latest_start,
                "interval_sec": interval,
                "metrics": trimmed_metrics,
            }

        return filtered
