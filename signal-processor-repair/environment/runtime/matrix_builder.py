"""
Report builder for signal processing output.

Generates structured output files including the anomaly report,
correlation matrix, and processing summary. Anomaly entries are
sorted for deterministic output ordering.
"""

import json
import os
import configparser


class MatrixBuilder:
    """Builds output reports from processing results."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._anomaly_path = config.get("output", "anomaly_path")
        self._correlation_path = config.get("output", "correlation_path")
        self._summary_path = config.get("output", "summary_path")

    def generate_reports(self, calibrated_readings, anomalies,
                         correlation_matrix, windows):
        """Generate all output reports."""
        anomaly_report = self._build_anomaly_report(anomalies)
        correlation_report = self._build_correlation_report(
            correlation_matrix
        )
        summary = self._build_summary(
            calibrated_readings, anomalies, correlation_matrix, windows
        )

        self._write_json(self._anomaly_path, anomaly_report)
        self._write_json(self._correlation_path, correlation_report)
        self._write_json(self._summary_path, summary)

        return anomaly_report, correlation_report, summary

    def _build_anomaly_report(self, anomalies):
        """Build sorted anomaly report.

        Anomalies are sorted by severity for prioritized response.
        """
        sorted_anomalies = sorted(
            anomalies,
            key=lambda a: (-a["severity_score"], a["timestamp"])
        )

        return {
            "total_anomalies": len(anomalies),
            "entries": sorted_anomalies,
        }

    def _build_correlation_report(self, correlation_matrix):
        """Build correlation matrix report."""
        entries = []
        for pair_key, data in sorted(correlation_matrix.items()):
            entries.append({
                "pair": data["pair"],
                "avg_correlation": data["avg_correlation"],
                "window_count": data["window_count"],
                "total_correlation": data["total_correlation"],
            })

        return {
            "total_pairs": len(entries),
            "entries": entries,
        }

    def _build_summary(self, calibrated_readings, anomalies,
                       correlation_matrix, windows):
        """Build processing summary."""
        stations = set(r["station_id"] for r in calibrated_readings)
        channels = set(r["channel"] for r in calibrated_readings)

        return {
            "total_readings": len(calibrated_readings),
            "stations_processed": sorted(stations),
            "channels": sorted(channels),
            "windows_created": len(windows),
            "total_anomalies": len(anomalies),
            "correlation_pairs": len(correlation_matrix),
            "anomalies_by_station": self._count_by_station(anomalies),
        }

    def _count_by_station(self, anomalies):
        """Count anomalies per station."""
        counts = {}
        for a in anomalies:
            sid = a["station_id"]
            counts[sid] = counts.get(sid, 0) + 1
        return counts

    def _write_json(self, path, data):
        """Write data as formatted JSON."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
