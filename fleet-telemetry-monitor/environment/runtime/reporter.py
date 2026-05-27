"""Report generator — assembles final alert report and summary.

Sorts and groups alerts by vehicle and severity, then produces
the final JSON outputs for the monitoring system.
"""
import configparser
import json
import os


class ReportGenerator:
    """Generates monitoring report from scored alerts."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._output_dir = self._config.get("fleet", "output_dir")

    def generate(self, scored_alerts):
        """Generate alert report and summary files.

        Alerts within each vehicle group are sorted by severity
        (highest first). Vehicle groups appear in numeric order
        by vehicle identifier.
        """
        os.makedirs(self._output_dir, exist_ok=True)

        # Group by vehicle
        grouped = {}
        for alert in scored_alerts:
            vid = alert["vehicle_id"]
            if vid not in grouped:
                grouped[vid] = []
            grouped[vid].append(alert)

        # Sort within each group by severity descending
        for vid in grouped:
            grouped[vid].sort(key=lambda a: a["severity"], reverse=True)

        # Build ordered alert list: vehicles sorted by identifier
        vehicle_order = sorted(grouped.keys())
        ordered_alerts = []
        for vid in vehicle_order:
            ordered_alerts.extend(grouped[vid])

        # Compute summary
        total_alerts = len(ordered_alerts)
        vehicles_affected = len(grouped)
        total_duration = sum(a["duration_windows"] for a in ordered_alerts)
        max_severity = max(a["severity"] for a in ordered_alerts) if ordered_alerts else 0.0
        total_spikes = sum(a["total_speed_spikes"] for a in ordered_alerts)

        # Write alerts
        alerts_path = os.path.join(self._output_dir, "alerts.json")
        with open(alerts_path, "w") as f:
            json.dump(ordered_alerts, f, indent=2)

        # Write summary
        summary = {
            "total_alerts": total_alerts,
            "vehicles_affected": vehicles_affected,
            "total_duration_windows": total_duration,
            "max_severity": round(max_severity, 4),
            "total_speed_spikes": total_spikes,
            "vehicle_order": vehicle_order,
        }
        summary_path = os.path.join(self._output_dir, "summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        return summary
