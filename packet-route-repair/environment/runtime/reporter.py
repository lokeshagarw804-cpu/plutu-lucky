"""Flow quality reporter — anomaly scoring and report generation.

Aggregates per-packet anomaly data into source-destination flow pairs,
computes anomaly scores based on configured weights, and produces
sorted flow reports with summary statistics.
"""
import configparser
import json


class FlowReporter:
    """Generates flow quality reports with anomaly scoring."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._weights = [
            float(w) for w in self._config.get("scoring", "weights").split(",")
        ]
        self._min_score = self._config.getfloat("scoring", "min_anomaly_score")

    def generate_report(self, analysis_results):
        """Generate flow report from per-packet analysis results.

        Groups packets by (source, destination), computes per-flow
        anomaly scores, and produces sorted output.

        Returns (flows_list, summary_dict).
        """
        flow_groups = self._group_by_flow(analysis_results)
        flows = []

        for (src, dst), packets in flow_groups.items():
            flow = self._compute_flow_metrics(src, dst, packets)
            if flow["anomaly_score"] >= self._min_score:
                flows.append(flow)

        flows = self._apply_normalization(flows)
        flows.sort(key=lambda f: (f["source_node"], -f["anomaly_score"]))

        summary = self._build_summary(flows)
        return flows, summary

    def _group_by_flow(self, results):
        """Group analysis results by (source, destination) pair."""
        groups = {}
        for record in results:
            key = (record["src"], record["dst"])
            groups.setdefault(key, []).append(record)
        return groups

    def _compute_flow_metrics(self, src, dst, packets):
        """Compute metrics for a single flow (src→dst pair).

        Anomaly score is a weighted combination of:
          - Loop ratio (weight[0]): fraction of packets with loops
          - Suboptimal ratio (weight[1]): fraction taking suboptimal paths
          - Cost deviation (weight[2]): normalized excess over optimal cost
        """
        loop_count = sum(1 for p in packets if p["has_loop"])
        suboptimal_count = sum(1 for p in packets if p["is_suboptimal"])
        total = len(packets)

        loop_ratio = loop_count / total if total > 0 else 0
        suboptimal_ratio = suboptimal_count / total if total > 0 else 0

        avg_cost = sum(p["path_cost"] for p in packets) / total if total > 0 else 0
        optimal = packets[0]["optimal_cost"] if packets else 1
        cost_deviation = (avg_cost - optimal) / optimal if optimal > 0 else 0
        cost_deviation = max(0, min(1, cost_deviation))

        score = (
            self._weights[0] * loop_ratio
            + self._weights[1] * suboptimal_ratio
            + self._weights[2] * cost_deviation
        )

        return {
            "source_node": src,
            "dest_node": dst,
            "anomaly_score": round(score, 4),
            "path_cost": int(avg_cost),
            "optimal_cost": int(optimal) if optimal != float("inf") else 0,
            "has_loop": loop_count > 0,
        }

    def _apply_normalization(self, flows):
        """Normalize anomaly scores by total accumulated cost per source.

        Divides each flow's score by the sum of path_costs across all
        destinations for that source, then rescales to [0, 1] range.
        """
        source_totals = {}
        for flow in flows:
            src = flow["source_node"]
            total_cost = flow["path_cost"]
            source_totals[src] = total_cost

        max_score = 0
        for flow in flows:
            src = flow["source_node"]
            divisor = source_totals[src] if source_totals[src] > 0 else 1
            flow["anomaly_score"] = round(
                flow["anomaly_score"] * flow["path_cost"] / divisor, 4
            )
            max_score = max(max_score, flow["anomaly_score"])

        if max_score > 0:
            for flow in flows:
                flow["anomaly_score"] = round(flow["anomaly_score"] / max_score, 4)

        return flows

    def _build_summary(self, flows):
        """Build summary statistics from final flow list."""
        total_flows = len(flows)
        loops = sum(1 for f in flows if f["has_loop"])
        suboptimal = sum(1 for f in flows if f["path_cost"] > f["optimal_cost"])
        scores = [f["anomaly_score"] for f in flows]
        max_score = max(scores) if scores else 0
        avg_score = round(sum(scores) / len(scores), 4) if scores else 0

        return {
            "total_flows": total_flows,
            "loops_detected": loops,
            "suboptimal_count": suboptimal,
            "max_anomaly_score": max_score,
            "avg_anomaly_score": avg_score,
        }
