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

    def test_ledger_state_exists(self):
        """Ledger state output file must be generated at the expected path."""
        assert os.path.isfile(LEDGER_STATE_PATH), (
            f"Expected output file at {LEDGER_STATE_PATH}"
        )

    def test_reconciliation_report_exists(self):
        """Reconciliation report output file must be generated."""
        assert os.path.isfile(RECONCILIATION_PATH), (
            f"Expected output file at {RECONCILIATION_PATH}"
        )

    def test_ledger_state_has_required_fields(self, ledger_state):
        """Ledger state must contain all documented schema fields."""
        required = ["stream_count", "total_events", "window_count",
                    "final_balances", "streams_processed"]
        for field in required:
            assert field in ledger_state, (
                f"Missing required field '{field}' in ledger_state.json"
            )

    def test_reconciliation_has_required_fields(self, reconciliation_report):
        """Reconciliation report must contain all documented schema fields."""
        required = ["total_anomalies", "anomalies", "windows_analyzed",
                    "has_high_severity"]
        for field in required:
            assert field in reconciliation_report, (
                f"Missing required field '{field}' in reconciliation_report.json"
            )


class TestStreamLoading:
    """Validates that all configured account streams are loaded."""

    def test_stream_count(self, ledger_state):
        """All 5 configured streams must be loaded including merchant type.

        The active_types in /app/runtime/config.ini lists savings, checking,
        credit, and merchant. Verify /app/runtime/loader.py correctly parses
        all entries from the comma-separated list.
        """
        assert ledger_state["stream_count"] == 5, (
            f"Expected 5 streams (savings, checking, credit, merchant) but "
            f"got {ledger_state['stream_count']}. Check how "
            "/app/runtime/loader.py parses the active_types config value — "
            "all items in the comma-separated list should be recognized."
        )

    def test_total_event_count(self, ledger_state):
        """System must process all 84 events from the 5 streams."""
        assert ledger_state["total_events"] == 84, (
            f"Expected 84 total events but got {ledger_state['total_events']}. "
            "If streams are missing, check account type filtering in "
            "/app/runtime/loader.py."
        )

    def test_merchant_stream_included(self, ledger_state):
        """The merchant-type stream (stream_gamma) must be in output."""
        assert "stream_gamma" in ledger_state["streams_processed"], (
            "stream_gamma (account_type=merchant) is missing from output. "
            "Check how /app/runtime/loader.py handles the active_types "
            "configuration — ensure each type is trimmed before comparison."
        )


class TestWindowAggregation:
    """Validates time-window balance computation."""

    def test_window_count(self, ledger_state):
        """Events should span exactly 4 time windows."""
        assert ledger_state["window_count"] == 4, (
            f"Expected 4 windows but got {ledger_state['window_count']}"
        )

    def test_final_balance_stream_alpha(self, ledger_state):
        """Stream alpha final balance must be 1900.0.

        This reflects correct window-close snapshot behavior rather than
        accumulated totals. Check /app/runtime/aggregator.py window
        balance update logic.
        """
        balance = ledger_state["final_balances"]["stream_alpha"]
        assert balance == 1900.0, (
            f"Expected stream_alpha final balance 1900.0 but got {balance}. "
            "If balance is inflated, check whether /app/runtime/aggregator.py "
            "accumulates across batch snapshots instead of using the final "
            "snapshot value for each window."
        )

    def test_final_balance_stream_gamma(self, ledger_state):
        """Stream gamma final balance must be 3380.0.

        Requires both correct stream loading and correct aggregation.
        """
        assert "stream_gamma" in ledger_state["final_balances"], (
            "stream_gamma missing from final_balances — check stream loading"
        )
        balance = ledger_state["final_balances"]["stream_gamma"]
        assert balance == 3380.0, (
            f"Expected stream_gamma final balance 3380.0 but got {balance}. "
            "This requires both correct account type filtering and correct "
            "window balance snapshot logic."
        )

    def test_final_balance_stream_epsilon(self, ledger_state):
        """Stream epsilon final balance must be 180.0."""
        balance = ledger_state["final_balances"]["stream_epsilon"]
        assert balance == 180.0, (
            f"Expected stream_epsilon final balance 180.0 but got {balance}. "
            "Check /app/runtime/aggregator.py — window balances should "
            "reflect the last event's running balance, not cumulative sums."
        )


class TestReconciliation:
    """Validates anomaly detection with strict thresholds."""

    def test_total_anomaly_count(self, reconciliation_report):
        """Reconciliation must detect exactly 5 anomalies.

        With the strict threshold (balance_threshold=100 from the
        reconciliation.strict section in /app/runtime/config.ini),
        all 5 streams should trigger anomaly flags. Check which
        config section /app/runtime/reconciler.py reads from.
        """
        count = reconciliation_report["total_anomalies"]
        assert count == 5, (
            f"Expected 5 anomalies but got {count}. The strict reconciliation "
            "parameters (reconciliation.strict section) use "
            "balance_threshold=100 and min_consecutive_windows=2. Check "
            "which section /app/runtime/reconciler.py reads — it should use "
            "reconciliation.strict, not reconciliation."
        )

    def test_epsilon_anomaly_detected(self, reconciliation_report):
        """Stream epsilon must be flagged as anomaly with medium severity.

        With strict threshold of 100, epsilon's balance (120-180 range)
        should trigger across multiple windows.
        """
        anomalies = reconciliation_report["anomalies"]
        epsilon_flags = [a for a in anomalies if a["stream_id"] == "stream_epsilon"]
        assert len(epsilon_flags) >= 1, (
            "stream_epsilon should be flagged as anomaly with strict "
            "threshold=100 (balance stays above 100 for consecutive windows). "
            "Check /app/runtime/reconciler.py config section — should read "
            "from reconciliation.strict."
        )
        assert epsilon_flags[0]["severity"] == "medium", (
            f"Expected medium severity for epsilon but got "
            f"'{epsilon_flags[0]['severity']}'"
        )

    def test_has_high_severity(self, reconciliation_report):
        """At least one anomaly must have high severity."""
        assert reconciliation_report["has_high_severity"] is True


class TestEventOrdering:
    """Validates deterministic event ordering across streams."""

    def test_all_streams_in_sorted_order(self, ledger_state):
        """Streams processed list must be lexicographically sorted."""
        streams = ledger_state["streams_processed"]
        assert streams == sorted(streams), (
            f"streams_processed should be sorted but got {streams}"
        )

    def test_deterministic_balance_with_concurrent_events(self, ledger_state):
        """Final balances must be deterministic when streams share timestamps.

        Multiple streams have events at timestamp 3600. The correct sort
        order is (timestamp, stream_id, seq) to ensure deterministic
        replay. Check /app/runtime/sorter.py sort key — it should include
        the stream identifier for tie-breaking.
        """
        # With correct ordering, batch boundaries are deterministic
        # which affects which events fall into which processing batch
        balance_alpha = ledger_state["final_balances"]["stream_alpha"]
        balance_delta = ledger_state["final_balances"]["stream_delta"]
        assert balance_alpha == 1900.0 and balance_delta == 2845.0, (
            f"Got stream_alpha={balance_alpha}, stream_delta={balance_delta}. "
            "Expected 1900.0 and 2845.0. Events at shared timestamps must be "
            "ordered by (timestamp, stream_id, seq) for deterministic replay. "
            "Check the sort key in /app/runtime/sorter.py."
        )
