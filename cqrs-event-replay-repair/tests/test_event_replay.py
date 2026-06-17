"""Validation tests for CQRS event replay engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
VIEW_PATH = os.path.join(OUTPUT_DIR, "materialized_view.json")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "replay_summary.json")


def load_view():
    """Load materialized view output."""
    with open(VIEW_PATH, "r") as f:
        return json.load(f)


def load_summary():
    """Load replay summary output."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


class TestOutputFileStructure:
    """Basic output file and structure validation."""

    def test_materialized_view_exists(self):
        """Materialized view output file must be generated."""
        assert os.path.isfile(VIEW_PATH)

    def test_replay_summary_exists(self):
        """Replay summary output file must be generated."""
        assert os.path.isfile(SUMMARY_PATH)

    def test_view_has_stream_keys(self):
        """Materialized view must contain stream identifiers."""
        view = load_view()
        assert isinstance(view, dict)
        assert len(view) > 0

    def test_summary_has_required_fields(self):
        """Summary must include required fields."""
        summary = load_summary()
        assert "total_events_processed" in summary
        assert "stream_count" in summary
        assert "streams" in summary
        assert "ordering_hash" in summary


class TestStreamCompleteness:
    """Validates all configured streams are present in output."""

    def test_all_three_streams_present(self):
        """All three configured aggregates must appear in the view."""
        view = load_view()
        expected_streams = {"orders", "inventory", "payments"}
        actual_streams = set(view.keys())
        missing = expected_streams - actual_streams
        assert not missing, (
            f"Missing streams in output: {missing}"
        )

    def test_stream_count_in_summary(self):
        """Summary must report exactly 3 active streams."""
        summary = load_summary()
        assert summary["stream_count"] == 3, (
            f"Expected 3 streams, got {summary['stream_count']}"
        )


class TestEventCounts:
    """Validates correct event counting per stream."""

    def test_total_events_processed(self):
        """Total events must equal 53."""
        summary = load_summary()
        assert summary["total_events_processed"] == 53, (
            f"Expected 53 total events, got {summary['total_events_processed']}"
        )

    def test_orders_event_count(self):
        """Orders stream must have exactly 19 events."""
        view = load_view()
        assert "orders" in view
        assert view["orders"]["event_count"] == 19, (
            f"Expected 19 order events, got {view['orders']['event_count']}"
        )

    def test_inventory_event_count(self):
        """Inventory stream must have exactly 18 events."""
        view = load_view()
        assert "inventory" in view
        assert view["inventory"]["event_count"] == 18, (
            f"Expected 18 inventory events, got {view['inventory']['event_count']}"
        )

    def test_payments_event_count(self):
        """Payments stream must have exactly 16 events."""
        view = load_view()
        assert "payments" in view
        assert view["payments"]["event_count"] == 16, (
            f"Expected 16 payment events, got {view['payments']['event_count']}"
        )


class TestMaterializedTotals:
    """Validates materialized view totals match expected values."""

    def test_order_total_value(self):
        """Total order value must be 815.25."""
        view = load_view()
        orders_total = view["orders"]["totals"]["total_order_value"]
        assert abs(orders_total - 815.25) < 0.01, (
            f"Expected total_order_value=815.25, got {orders_total}"
        )

    def test_order_count(self):
        """Order count must be exactly 5."""
        view = load_view()
        order_count = view["orders"]["totals"]["order_count"]
        assert order_count == 5, (
            f"Expected order_count=5, got {order_count}"
        )

    def test_payment_captured_total(self):
        """Captured payment total must be 815.25."""
        view = load_view()
        captured = view["payments"]["totals"]["captured_total"]
        assert abs(captured - 815.25) < 0.01, (
            f"Expected captured_total=815.25, got {captured}"
        )

    def test_inventory_total_stock(self):
        """Total stock must equal 470."""
        view = load_view()
        total_stock = view["inventory"]["totals"]["total_stock"]
        assert total_stock == 470, (
            f"Expected total_stock=470, got {total_stock}"
        )


class TestDeterministicOrdering:
    """Validates deterministic event ordering across streams."""

    def test_ordering_hash_deterministic(self):
        """Ordering hash must match the expected deterministic sequence.

        The hash captures the full event ordering including stream
        provenance at each position in the global sequence.
        """
        summary = load_summary()
        expected_hash = "d744fb63ad2a3a5a"
        actual_hash = summary["ordering_hash"]
        assert actual_hash == expected_hash, (
            f"Ordering hash mismatch: expected '{expected_hash}', "
            f"got '{actual_hash}'"
        )

    def test_payment_settled_total(self):
        """Settled payment total must be 747.15."""
        view = load_view()
        settled = view["payments"]["totals"]["settled_total"]
        assert abs(settled - 747.15) < 0.01, (
            f"Expected settled_total=747.15, got {settled}"
        )
