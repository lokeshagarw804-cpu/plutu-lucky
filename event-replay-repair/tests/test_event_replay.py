"""Tests for the event replay materialization system.

Validates that the aggregate summary and event timeline are correctly
produced from the event streams after all processing stages complete.
"""
import json
import os

SUMMARY_PATH = "/app/runtime/output/aggregate_summary.json"
TIMELINE_PATH = "/app/runtime/output/event_timeline.json"


def load_summary():
    """Load the aggregate summary output."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def load_timeline():
    """Load the event timeline output."""
    with open(TIMELINE_PATH, "r") as f:
        return json.load(f)


# --- EASY TESTS (pass even with buggy code) ---

class TestOutputFilesExist:
    """Verify that the system produces the expected output files."""

    def test_summary_file_exists(self):
        """The aggregate_summary.json file must be created in the output directory."""
        assert os.path.isfile(SUMMARY_PATH), (
            f"Expected output file not found at {SUMMARY_PATH}"
        )

    def test_timeline_file_exists(self):
        """The event_timeline.json file must be created in the output directory."""
        assert os.path.isfile(TIMELINE_PATH), (
            f"Expected output file not found at {TIMELINE_PATH}"
        )

    def test_summary_has_required_top_level_fields(self):
        """The summary must contain total_orders, total_events_processed, total_net_revenue, orders."""
        data = load_summary()
        for field in ["total_orders", "total_events_processed", "total_net_revenue", "orders"]:
            assert field in data, (
                f"Missing required top-level field '{field}' in aggregate_summary.json"
            )

    def test_timeline_has_required_structure(self):
        """The timeline must contain total_events and entries fields."""
        data = load_timeline()
        assert "total_events" in data, "Missing 'total_events' in event_timeline.json"
        assert "entries" in data, "Missing 'entries' in event_timeline.json"
        assert isinstance(data["entries"], list), "'entries' must be a list"


# --- MEDIUM TESTS (require 1-2 bug fixes) ---

class TestStreamFiltering:
    """Verify that all configured event streams are included in processing."""

    def test_refund_events_in_timeline(self):
        """Refund events must appear in the timeline when the refunds stream is configured.

        The system should include all three configured streams: orders, payments, and refunds.
        Check /app/runtime/loader.py for stream filtering logic.
        """
        data = load_timeline()
        stream_ids = set(e["stream_id"] for e in data["entries"])
        assert "refunds" in stream_ids, (
            "Refund events missing from timeline. The refunds stream should be loaded "
            "- check how event_streams config value is parsed in /app/runtime/loader.py"
        )

    def test_total_events_includes_all_streams(self):
        """Total event count must reflect events from all three streams (orders + payments + refunds).

        Expected: 14 order events + 7 payment events + 3 refund events = 24 total.
        """
        data = load_timeline()
        assert data["total_events"] == 24, (
            f"Expected 24 total events (14 orders + 7 payments + 3 refunds), "
            f"got {data['total_events']}. Check stream loading in /app/runtime/loader.py"
        )

    def test_orders_with_refunds_have_correct_status(self):
        """Orders that received refunds must show status 'partially_refunded'.

        ORD-1001, ORD-1003, and ORD-1006 have refund events.
        """
        data = load_summary()
        orders_map = {o["order_id"]: o for o in data["orders"]}
        refunded_ids = ["ORD-1001", "ORD-1003", "ORD-1006"]
        for oid in refunded_ids:
            assert oid in orders_map, f"Order {oid} missing from summary"
            assert orders_map[oid]["status"] == "partially_refunded", (
                f"Order {oid} should have status 'partially_refunded', "
                f"got '{orders_map[oid]['status']}'"
            )


# --- HARD TESTS (require 3-4 bug fixes together) ---

class TestAggregateAccuracy:
    """Verify that aggregate financial calculations are correct."""

    def test_net_revenue_for_refunded_order(self):
        """Net revenue must equal payment minus refund for each order.

        ORD-1001: payment 37.50 - refund 12.50 = net 25.00
        Requires correct stream loading, batch processing, and accumulation logic.
        """
        data = load_summary()
        orders_map = {o["order_id"]: o for o in data["orders"]}
        ord1001 = orders_map["ORD-1001"]
        assert ord1001["payment_amount"] == 37.50, (
            f"ORD-1001 payment_amount should be 37.50, got {ord1001['payment_amount']}"
        )
        assert ord1001["refund_amount"] == 12.50, (
            f"ORD-1001 refund_amount should be 12.50, got {ord1001['refund_amount']}"
        )
        assert ord1001["net_revenue"] == 25.00, (
            f"ORD-1001 net_revenue should be 25.00, got {ord1001['net_revenue']}"
        )

    def test_total_net_revenue(self):
        """Total net revenue across all orders must be correctly computed.

        Sum of all (payment - refund) values for 7 orders.
        ORD-1001: 37.50 - 12.50 = 25.00
        ORD-1002: 70.00 - 0.00 = 70.00
        ORD-1003: 62.50 - 25.00 = 37.50
        ORD-1004: 90.00 - 0.00 = 90.00
        ORD-1005: 57.50 - 0.00 = 57.50
        ORD-1006: 35.00 - 8.75 = 26.25
        ORD-1007: 33.75 - 0.00 = 33.75
        Total: 340.00
        """
        data = load_summary()
        assert data["total_net_revenue"] == 340.00, (
            f"Expected total_net_revenue of 340.00, got {data['total_net_revenue']}. "
            f"Check batch accumulation logic in /app/runtime/projector.py"
        )

    def test_timeline_deterministic_ordering(self):
        """Events with identical timestamps must be ordered by stream_id then seq.

        At timestamp 2024-03-01T11:00:00Z, both orders (evt_007, seq=7) and
        refunds (evt_201, seq=1) have events. Correct order: orders first
        (stream_id 'orders' < 'refunds' lexicographically), so evt_007 before evt_201.
        Check sort key in /app/runtime/correlator.py - ordering must include stream_id.
        """
        data = load_timeline()
        entries = data["entries"]
        timestamp_11 = [e for e in entries if e["timestamp"] == "2024-03-01T11:00:00Z"]
        assert len(timestamp_11) == 2, (
            f"Expected 2 events at 11:00:00Z, got {len(timestamp_11)}. "
            "Check that all streams are loaded."
        )
        assert timestamp_11[0]["stream_id"] == "orders", (
            f"At timestamp 11:00:00Z, first event should be from 'orders' stream "
            f"(alphabetically before 'refunds'), got '{timestamp_11[0]['stream_id']}'. "
            f"Check sort tiebreaker in /app/runtime/correlator.py"
        )
        assert timestamp_11[1]["stream_id"] == "refunds", (
            f"At timestamp 11:00:00Z, second event should be from 'refunds' stream, "
            f"got '{timestamp_11[1]['stream_id']}'"
        )
