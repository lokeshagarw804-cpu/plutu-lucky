"""Report generator — produces final anomaly report and fleet summary.

Assembles per-vehicle anomaly lists into two output files:
- anomalies.json: full list of detected anomalies with vehicle info
- summary.json: fleet-level aggregate statistics
"""
import json
import os


class ReportGenerator:
    """Generates anomaly report files."""

    def __init__(self, output_dir):
        self._output_dir = output_dir

    def generate(self, fleet_anomalies):
        """Write anomaly report and summary to output files.

        Args:
            fleet_anomalies: dict {vehicle_id: [anomaly_dicts]}
        """
        os.makedirs(self._output_dir, exist_ok=True)

        # Build flat anomaly list sorted by vehicle then score descending
        all_anomalies = []
        for vehicle_id in sorted(fleet_anomalies.keys()):
            vehicle_anoms = fleet_anomalies[vehicle_id]
            # Sort by fused_score descending within each vehicle
            sorted_anoms = sorted(
                vehicle_anoms, key=lambda a: a["fused_score"], reverse=True
            )
            for anom in sorted_anoms:
                entry = {"vehicle_id": vehicle_id}
                entry.update(anom)
                all_anomalies.append(entry)

        # Write anomalies
        with open(os.path.join(self._output_dir, "anomalies.json"), "w") as f:
            json.dump(all_anomalies, f, indent=2)

        # Compute summary
        total_anomalies = len(all_anomalies)
        vehicles_affected = len([
            v for v, anoms in fleet_anomalies.items() if len(anoms) > 0
        ])
        severity_counts = {"warning": 0, "critical": 0, "emergency": 0}
        max_score = 0.0
        total_score = 0.0

        for anom in all_anomalies:
            sev = anom["severity"]
            if sev in severity_counts:
                severity_counts[sev] += 1
            if anom["fused_score"] > max_score:
                max_score = anom["fused_score"]
            total_score += anom["fused_score"]

        avg_score = round(total_score / total_anomalies, 4) if total_anomalies > 0 else 0.0

        summary = {
            "total_anomalies": total_anomalies,
            "vehicles_affected": vehicles_affected,
            "severity_counts": severity_counts,
            "max_fused_score": round(max_score, 4),
            "avg_fused_score": avg_score,
            "fleet_size": 4,
        }

        with open(os.path.join(self._output_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=2)
