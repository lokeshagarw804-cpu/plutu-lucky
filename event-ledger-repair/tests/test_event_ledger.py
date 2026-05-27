"""Validation tests for event ledger replay engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
LEDGER_STATE_PATH = os.path.join(OUTPUT_DIR, "ledger_state.json")
RECONCILIATION_PATH = os.path.join(OUTPUT_DIR, "reconciliation_report.json")


@pytest.fixture(scope="module")
def ledger_state():
    """Load ledger state output."""
    with open(LEDGER_STATE_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def reconciliation_report():
    """Load reconciliation report output."""
    with open(RECONCILIATION_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file structure validation."""

    def test_ledger_state_file_generated(self):
        """The ledger state output file must exist at the expected path."""
        assert os.path.isfile(LEDGER_STATE_PATH), (
            f"Expected output at {LEDGER_STATE_PATH}"
        )

    def test_reconciliation_report_file_generated(self):
        """The reconciliation report output file must exist."""
        assert os.path.isfile(RECONCILIATION_PATH), (
            f"Expected output at {RECONCILIATION_PATH}"
        )

    def test_ledger_state_schema_fields(self, ledger_state):
        """Ledger state must contain all required schema fields."""
        required = ["stream_count", "total_events", "window_count",
                    "final_balances", "streams_processed"]
        for field in required:
            assert field in ledger_state, (
                f"Missing required field '{field}' in ledger_state.json"
            )

    def test_reconciliation_report_schema_fields(self, reconciliation_report):
        """Reconciliation report must contain all required schema fields."""
        required = ["total_anomalies", "anomalies", "windows_analyzed",
                    "has_high_severity"]
        for field in required:
            assert field in reconciliation_report, (
                f"Missing required field '{field}' in reconciliation_report.json"
            )


class TestStreamProcessing:
    """Validates correct stream loading and event processing."""

    def test_all_configured_streams_loaded(self, ledger_state):
        """All streams matching configured account types must be loaded.

        The data directory contains streams for multiple account types.
        All matching types should appear in the output.
        """
        assert ledger_state["stream_count"] == 5, (
            f"Expected 5 streams but got {ledger_state['stream_count']}. "
            "Check how the loader parses the active_types configuration "
            "value in /app/runtime/loader.py."
        )

    def test_complete_event_ingestion(self, ledger_state):
        """All events from loaded streams must be processed."""
        assert ledger_state["total_events"] == 84, (
            f"Expected 84 total events but got {ledger_state['total_events']}."
        )

    def test_merchant_account_stream_present(self, ledger_state):
        """The merchant-type stream must appear in processed streams."""
        assert "stream_gamma" in ledger_state["streams_processed"], (
            "stream_gamma is missing from processed streams."
        )

    def test_window_count_matches_time_range(self, ledger_state):
        """Events should produce exactly 4 time windows."""
        assert ledger_state["window_count"] == 4


class TestBalanceComputation:
    """Validates per-stream balance accuracy in window snapshots."""

    def test_stream_alpha_final_balance(self, ledger_state):
        """Stream alpha final balance must be 1900.0.

        The balance represents the running total after all deposits and
        withdrawals. Verify that the aggregator correctly captures the
        final account state for each window.
        """
        balance = ledger_state["final_balances"]["stream_alpha"]
        assert balance == 1900.0, (
            f"stream_alpha balance is {balance}, expected 1900.0. "
            "Check how /app/runtime/aggregator.py finalizes per-window "
            "balance values from the accumulated event snapshots."
        )

    def test_stream_beta_final_balance(self, ledger_state):
        """Stream beta final balance must be 2275.0."""
        balance = ledger_state["final_balances"]["stream_beta"]
        assert balance == 2275.0, (
            f"stream_beta balance is {balance}, expected 2275.0"
        )

    def test_stream_gamma_final_balance(self, ledger_state):
        """Stream gamma (merchant) final balance must be 3380.0."""
        assert "stream_gamma" in ledger_state["final_balances"], (
            "stream_gamma is missing from final_balances"
        )
        balance = ledger_state["final_balances"]["stream_gamma"]
        assert balance == 3380.0, (
            f"stream_gamma balance is {balance}, expected 3380.0"
        )

    def test_stream_delta_final_balance(self, ledger_state):
        """Stream delta final balance must be 2845.0."""
        balance = ledger_state["final_balances"]["stream_delta"]
        assert balance == 2845.0, (
            f"stream_delta balance is {balance}, expected 2845.0"
        )

    def test_stream_epsilon_final_balance(self, ledger_state):
        """Stream epsilon final balance must be 180.0.

        Epsilon has relatively small transactions. Its correct final
        state helps validate that the balance computation works for
        both large and small account values.
        """
        balance = ledger_state["final_balances"]["stream_epsilon"]
        assert balance == 180.0, (
            f"stream_epsilon balance is {balance}, expected 180.0"
        )


class TestReconciliationDetection:
    """Validates anomaly detection sensitivity and classification."""

    def test_anomaly_count(self, reconciliation_report):
        """Reconciliation must detect exactly 5 anomalies.

        All streams should trigger anomaly flags at the appropriate
        sensitivity level. Review which configuration parameters the
        reconciler uses for threshold and minimum window requirements.
        """
        count = reconciliation_report["total_anomalies"]
        assert count == 5, (
            f"Expected 5 anomalies but got {count}. Check the threshold "
            "and minimum consecutive window settings loaded by the "
            "reconciler from /app/runtime/config.ini."
        )

    def test_small_balance_stream_flagged(self, reconciliation_report):
        """Stream epsilon with moderate balance must be flagged as anomaly."""
        anomalies = reconciliation_report["anomalies"]
        epsilon_flags = [
            a for a in anomalies if a["stream_id"] == "stream_epsilon"
        ]
        assert len(epsilon_flags) >= 1, (
            "stream_epsilon should trigger an anomaly flag. Its balance "
            "stays above the production threshold for multiple consecutive "
            "windows."
        )

    def test_epsilon_severity_medium(self, reconciliation_report):
        """Stream epsilon anomaly should have medium severity."""
        anomalies = reconciliation_report["anomalies"]
        epsilon_flags = [
            a for a in anomalies if a["stream_id"] == "stream_epsilon"
        ]
        assert len(epsilon_flags) >= 1
        assert epsilon_flags[0]["severity"] == "medium", (
            f"Expected medium severity for epsilon, got "
            f"'{epsilon_flags[0]['severity']}'"
        )

    def test_high_severity_anomalies_present(self, reconciliation_report):
        """At least one anomaly must have high severity."""
        assert reconciliation_report["has_high_severity"] is True

    def test_streams_processed_complete_and_sorted(self, ledger_state):
        """All 5 streams must appear in sorted order."""
        streams = ledger_state["streams_processed"]
        assert len(streams) == 5
        assert streams == sorted(streams)
