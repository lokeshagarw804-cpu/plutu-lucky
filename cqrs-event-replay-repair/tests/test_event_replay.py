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
        """Materialized view output file must be generated at expected path."""
        assert os.path.isfile(VIEW_PATH), (
            f"Expected materialized view at {VIEW_PATH}"
        )

    def test_replay_summary_exists(self):
        """Replay summary output file must be generated at expected path."""
        assert os.path.isfile(SUMMARY_PATH), (
            f"Expected replay summary at {SUMMARY_PATH}"
        )

    def test_view_has_stream_keys(self):
        """Materialized view must contain top-level stream identifiers."""
        view = load_view()
        assert isinstance(view, dict), "View must be a JSON object"
        assert len(view) > 0, "View must contain at least one stream"

    def test_summary_has_required_fields(self):
        """Summary must include total_events_processed, stream_count, streams, ordering_hash."""
        summary = load_summary()
        assert "total_events_processed" in summary
        assert "stream_count" in summary
        assert "streams" in summary
        assert "ordering_hash" in summary


class TestStreamCompleteness:
    """Validates all configured streams are present in output."""

    def test_all_three_streams_present(self):
        """All three configured aggregates (orders, inventory, payments) must appear.

        The active_aggregates setting in /app/runtime/config.ini lists all
        three streams. Check that /app/runtime/loader.py correctly parses
        the comma-separated list including items with surrounding whitespace.
        """
        view = load_view()
        expected_streams = {"orders", "inventory", "payments"}
        actual_streams = set(view.keys())
        missing = expected_streams - actual_streams
        assert not missing, (
            f"Missing streams: {missing}. The loader in /app/runtime/loader.py "
            f"must handle whitespace when parsing active_aggregates from "
            f"/app/runtime/config.ini — check how the comma-separated list is split."
        )

    def test_stream_count_in_summary(self):
        """Summary must report exactly 3 active streams."""
        summary = load_summary()
        assert summary["stream_count"] == 3, (
            f"Expected 3 streams but got {summary['stream_count']}. "
            f"Verify /app/runtime/loader.py parses all entries from "
            f"active_aggregates in /app/runtime/config.ini."
        )


class TestEventCounts:
    """Validates correct event counting per stream."""

    def test_total_events_processed(self):
        """Total events must equal sum of all stream events (53 total)."""
        summary = load_summary()
        assert summary["total_events_processed"] == 53, (
            f"Expected 53 total events but got {summary['total_events_processed']}. "
            f"All three streams must be loaded and their events counted once each."
        )

    def test_orders_event_count(self):
        """Orders stream must process exactly 19 events."""
        view = load_view()
        assert "orders" in view, "Orders stream missing from view"
        assert view["orders"]["event_count"] == 19, (
            f"Expected 19 order events but got {view['orders']['event_count']}"
        )

    def test_inventory_event_count(self):
        """Inventory stream must process exactly 18 events."""
        view = load_view()
        assert "inventory" in view, "Inventory stream missing from view"
        assert view["inventory"]["event_count"] == 18, (
            f"Expected 18 inventory events but got {view['inventory']['event_count']}"
        )

    def test_payments_event_count(self):
        """Payments stream must process exactly 16 events."""
        view = load_view()
        assert "payments" in view, "Payments stream missing from view"
        assert view["payments"]["event_count"] == 16, (
            f"Expected 16 payment events but got {view['payments']['event_count']}"
        )


class TestMaterializedTotals:
    """Validates materialized view totals use last-write-wins semantics."""

    def test_order_total_value(self):
        """Total order value must be 815.25 (sum of 5 orders, counted once).

        The materializer must use the final batch snapshot (latest mode)
        rather than accumulating totals across all batch snapshots. Check
        which config section /app/runtime/materializer.py reads
        snapshot_mode from — it should use replay.strict (latest), not
        replay (cumulative).
        """
        view = load_view()
        orders_total = view["orders"]["totals"]["total_order_value"]
        assert abs(orders_total - 815.25) < 0.01, (
            f"Expected total_order_value=815.25 but got {orders_total}. "
            f"If the value is inflated (e.g. >1000), the materializer is "
            f"summing across batch snapshots instead of using the final snapshot. "
            f"Check which config section /app/runtime/materializer.py reads "
            f"snapshot_mode from — replay.strict has 'latest', not replay."
        )

    def test_order_count(self):
        """Order count must be exactly 5."""
        view = load_view()
        order_count = view["orders"]["totals"]["order_count"]
        assert order_count == 5, (
            f"Expected order_count=5 but got {order_count}. "
            f"Totals should reflect final state, not accumulated across batches."
        )

    def test_payment_captured_total(self):
        """Captured payment total must be 815.25."""
        view = load_view()
        captured = view["payments"]["totals"]["captured_total"]
        assert abs(captured - 815.25) < 0.01, (
            f"Expected captured_total=815.25 but got {captured}. "
            f"Check materializer snapshot_mode configuration."
        )

    def test_inventory_total_stock(self):
        """Total stock additions must equal 470 (initial + replenished)."""
        view = load_view()
        total_stock = view["inventory"]["totals"]["total_stock"]
        assert total_stock == 470, (
            f"Expected total_stock=470 but got {total_stock}. "
            f"Materializer must use final snapshot, not sum across batches."
        )


class TestDeterministicOrdering:
    """Validates deterministic event ordering across streams."""

    def test_ordering_hash_deterministic(self):
        """Ordering hash must match the expected deterministic sequence.

        Events with identical timestamps from different streams must be
        ordered by stream_id then seq for a fully deterministic replay.
        The sequencer in /app/runtime/sequencer.py must sort by
        (timestamp, stream_id, seq) — not just (timestamp, seq) — because
        seq values are local to each stream and cannot break ties across
        different streams.
        """
        summary = load_summary()
        expected_hash = "d744fb63ad2a3a5a"
        actual_hash = summary["ordering_hash"]
        assert actual_hash == expected_hash, (
            f"Ordering hash mismatch: expected '{expected_hash}' but got "
            f"'{actual_hash}'. Events with the same timestamp from different "
            f"streams must be ordered by stream_id for deterministic replay. "
            f"Check the sort key in /app/runtime/sequencer.py — it should "
            f"include stream_id between timestamp and seq."
        )

    def test_payment_settled_total(self):
        """Settled payment total must be 747.15 (requires correct ordering and snapshot)."""
        view = load_view()
        settled = view["payments"]["totals"]["settled_total"]
        assert abs(settled - 747.15) < 0.01, (
            f"Expected settled_total=747.15 but got {settled}. "
            f"This requires both correct event ordering and latest-snapshot mode."
        )
