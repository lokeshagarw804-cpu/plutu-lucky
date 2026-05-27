"""Report builder — generates pipeline health report from analysis results.

Assembles all analysis outputs into a structured JSON report with
summary statistics and per-segment details.
"""
import json
import os


class ReportBuilder:
    """Builds the final pipeline health report."""

    def build_report(self, segments, flow_stats, pressure_anomalies,
                     flow_anomalies, classifications, segment_order):
        """Assemble complete pipeline health report.

        Returns dict with summary and per-segment detail sections.
        """
        # Count totals
        total_pressure_anomalies = sum(
            len(v) for v in pressure_anomalies.values()
        )
        total_flow_anomalies = sum(
            len(v) for v in flow_anomalies.values()
        )
        total_leaks = 0
        total_blockages = 0
        max_severity = 0.0

        for seg_id, classes in classifications.items():
            for entry in classes:
                if entry["classification"] == "leak":
                    total_leaks += 1
                elif entry["classification"] == "blockage":
                    total_blockages += 1
                if entry["severity"] > max_severity:
                    max_severity = entry["severity"]

        # Build per-segment details in network order
        segment_details = []
        for seg_id in segment_order:
            if seg_id not in segments:
                continue
            detail = {
                "segment_id": seg_id,
                "length_m": segments[seg_id]["length_m"],
                "diameter_m": segments[seg_id]["diameter_m"],
                "flow_stats": flow_stats.get(seg_id, {}),
                "pressure_anomaly_count": len(
                    pressure_anomalies.get(seg_id, [])
                ),
                "flow_anomaly_count": len(flow_anomalies.get(seg_id, [])),
                "classifications": classifications.get(seg_id, []),
            }
            segment_details.append(detail)

        report = {
            "segment_order": segment_order,
            "total_segments": len(segment_order),
            "total_pressure_anomalies": total_pressure_anomalies,
            "total_flow_anomalies": total_flow_anomalies,
            "total_leaks": total_leaks,
            "total_blockages": total_blockages,
            "max_severity": round(max_severity, 4),
            "segments": segment_details,
        }
        return report

    def write_report(self, report, output_dir):
        """Write report to JSON file."""
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, "pipeline_report.json")
        with open(path, "w") as f:
            json.dump(report, f, indent=2)

    def write_flow_summary(self, flow_stats, segment_order, output_dir):
        """Write flow summary to separate JSON file."""
        os.makedirs(output_dir, exist_ok=True)
        summary = {
            "segment_order": segment_order,
            "segments": {
                seg_id: flow_stats[seg_id]
                for seg_id in segment_order
                if seg_id in flow_stats
            },
            "total_volume": round(
                sum(v["total_volume"] for v in flow_stats.values()), 4
            ),
        }
        path = os.path.join(output_dir, "flow_summary.json")
        with open(path, "w") as f:
            json.dump(summary, f, indent=2)
