"""Report generator — produces reconciliation summary and ledger state.

Assembles final output from window aggregation and anomaly detection
results. Produces two output files: the ledger state summary and
the reconciliation anomaly report.
"""
import json
import os


class ReportGenerator:
    """Generates JSON output reports from processed ledger data."""

    def __init__(self, output_dir):
        self._output_dir = output_dir

    def generate(self, windows, anomalies, stream_count, total_events):
        """Generate ledger state and reconciliation reports.

        Writes two JSON files to the configured output directory.
        """
        os.makedirs(self._output_dir, exist_ok=True)

        ledger_state = self._build_ledger_state(
            windows, stream_count, total_events
        )
        reconciliation_report = self._build_reconciliation_report(
            anomalies, windows
        )

        state_path = os.path.join(self._output_dir, "ledger_state.json")
        with open(state_path, "w") as f:
            json.dump(ledger_state, f, indent=2)

        report_path = os.path.join(self._output_dir, "reconciliation_report.json")
        with open(report_path, "w") as f:
            json.dump(reconciliation_report, f, indent=2)

    def _build_ledger_state(self, windows, stream_count, total_events):
        """Build the ledger state summary."""
        # Compute final balances from last window that has data for each stream
        final_balances = {}
        for window in windows:
            for stream_id, balance in window["balances"].items():
                final_balances[stream_id] = balance

        total_event_count = sum(w["event_count"] for w in windows)

        return {
            "stream_count": stream_count,
            "total_events": total_event_count,
            "window_count": len(windows),
            "final_balances": final_balances,
            "streams_processed": sorted(final_balances.keys()),
        }

    def _build_reconciliation_report(self, anomalies, windows):
        """Build the reconciliation anomaly report."""
        return {
            "total_anomalies": len(anomalies),
            "anomalies": anomalies,
            "windows_analyzed": len(windows),
            "has_high_severity": any(
                a["severity"] == "high" for a in anomalies
            ),
        }
