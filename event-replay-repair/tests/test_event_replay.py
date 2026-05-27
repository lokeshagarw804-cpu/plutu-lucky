"""Validation tests for event replay engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
SNAPSHOT_PATH = os.path.join(OUTPUT_DIR, "entity_snapshot.json")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "replay_summary.json")


@pytest.fixture(scope="module")
def snapshot_data():
    """Load entity snapshot output."""
    with open(SNAPSHOT_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def summary_data():
    """Load replay summary output."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def get_entity(snapshot, entity_id):
    """Helper to find entity by ID in snapshot."""
    for ent in snapshot["entities"]:
        if ent["entity_id"] == entity_id:
            return ent
    return None


class TestOutputFiles:
    """Basic output file structure validation."""

    def test_snapshot_file_exists(self):
        """Entity snapshot output file must be generated."""
        assert os.path.isfile(SNAPSHOT_PATH), (
            f"Expected output file at {SNAPSHOT_PATH}"
        )

    def test_summary_file_exists(self):
        """Replay summary output file must be generated."""
        assert os.path.isfile(SUMMARY_PATH), (
            f"Expected output file at {SUMMARY_PATH}"
        )

    def test_snapshot_has_required_fields(self, snapshot_data):
        """Snapshot must contain version, total_entities, and entities array."""
        assert "version" in snapshot_data
        assert "total_entities" in snapshot_data
        assert "entities" in snapshot_data
        assert isinstance(snapshot_data["entities"], list)

    def test_summary_has_required_fields(self, summary_data):
        """Summary must contain all documented metadata fields."""
        assert "total_events_processed" in summary_data
        assert "total_streams" in summary_data
        assert "batch_count" in summary_data
        assert "batch_size" in summary_data
        assert "entity_count" in summary_data
        assert "streams_loaded" in summary_data


class TestStreamLoading:
    """Validates that all configured streams are loaded correctly."""

    def test_total_streams_loaded(self, summary_data):
        """All 4 configured streams must be loaded including fulfillment.

        The active_streams config in /app/runtime/config.ini lists 4 streams.
        Check that /app/runtime/loader.py correctly parses all stream names
        from the comma-separated configuration value.
        """
        assert summary_data["total_streams"] == 4, (
            f"Expected 4 streams loaded but got {summary_data['total_streams']}. "
            "Check how /app/runtime/loader.py parses the active_streams "
            "config value — all entries in the comma-separated list should "
            "be recognized."
        )

    def test_fulfillment_stream_present(self, summary_data):
        """The stream_fulfillment source must appear in loaded streams."""
        assert "stream_fulfillment" in summary_data["streams_loaded"], (
            "stream_fulfillment is missing from streams_loaded. "
            "Verify that /app/runtime/loader.py handles all entries in the "
            "active_streams comma-separated list in /app/runtime/config.ini."
        )

    def test_total_events_processed(self, summary_data):
        """Total event count must reflect all 4 streams (57 events)."""
        assert summary_data["total_events_processed"] == 57, (
            f"Expected 57 total events but got "
            f"{summary_data['total_events_processed']}. This count should "
            "include events from all 4 configured streams."
        )


class TestBatchProcessing:
    """Validates incremental batch processing configuration."""

    def test_batch_size_from_incremental_config(self, summary_data):
        """Batch size must be 25 as defined in replay.incremental section.

        The replay.incremental section in /app/runtime/config.ini sets
        batch_size=25. Check that /app/runtime/sequencer.py reads from
        the correct configuration section.
        """
        assert summary_data["batch_size"] == 25, (
            f"Expected batch_size=25 but got {summary_data['batch_size']}. "
            "The sequencer should read batch_size from the "
            "replay.incremental config section in /app/runtime/config.ini, "
            "not from the base replay section."
        )

    def test_batch_count(self, summary_data):
        """With 57 events and batch_size=25, expect 3 batches."""
        assert summary_data["batch_count"] == 3, (
            f"Expected 3 batches but got {summary_data['batch_count']}. "
            "With 57 events and batch_size=25, there should be ceil(57/25)=3 "
            "batches."
        )


class TestGaugeFieldSemantics:
    """Validates last-write-wins semantics for gauge-type fields."""

    def test_order_total_not_accumulated(self, snapshot_data):
        """Entity ent_101 order_total must be 175.00 (last value, not sum).

        Gauge fields use last-write-wins: only the most recent event value
        is retained. If order_total shows 325.00, the aggregator is
        incorrectly summing across events instead of overwriting.
        """
        ent = get_entity(snapshot_data, "ent_101")
        assert ent is not None, "Entity ent_101 not found in snapshot"
        order_total = ent["fields"].get("order_total")
        assert order_total == 175.00, (
            f"Expected ent_101 order_total=175.00 but got {order_total}. "
            "Gauge-type fields should use last-write-wins semantics. "
            "Check /app/runtime/aggregator.py for how gauge fields are applied "
            "— they should overwrite, not accumulate."
        )

    def test_payment_amount_last_write(self, snapshot_data):
        """Entity ent_101 payment_amount must be -50.00 (refund is last event)."""
        ent = get_entity(snapshot_data, "ent_101")
        assert ent is not None
        payment = ent["fields"].get("payment_amount")
        assert payment == -50.00, (
            f"Expected ent_101 payment_amount=-50.00 but got {payment}. "
            "The refund event (pay_010) at timestamp 3600 should overwrite "
            "the earlier payment value using last-write-wins gauge semantics."
        )

    def test_entity_102_order_total(self, snapshot_data):
        """Entity ent_102 order_total must be 89.99 (single confirmed value)."""
        ent = get_entity(snapshot_data, "ent_102")
        assert ent is not None
        order_total = ent["fields"].get("order_total")
        assert order_total == 89.99, (
            f"Expected ent_102 order_total=89.99 but got {order_total}."
        )


class TestFulfillmentStatus:
    """Validates fulfillment stream integration and status projection."""

    def test_entity_101_fulfillment_dispatched(self, snapshot_data):
        """Entity ent_101 must show fulfillment_status='dispatched' from
        the fulfillment stream (timestamp 2250), which is later than the
        inventory shipped event (timestamp 2200).
        """
        ent = get_entity(snapshot_data, "ent_101")
        assert ent is not None
        status = ent["fields"].get("fulfillment_status")
        assert status == "dispatched", (
            f"Expected ent_101 fulfillment_status='dispatched' but got "
            f"'{status}'. The stream_fulfillment events must be loaded and "
            "the latest status event should win. Check that all streams in "
            "/app/runtime/config.ini active_streams list are parsed correctly."
        )

    def test_entity_105_fulfillment_dispatched(self, snapshot_data):
        """Entity ent_105 must show dispatched status from fulfillment stream."""
        ent = get_entity(snapshot_data, "ent_105")
        assert ent is not None
        status = ent["fields"].get("fulfillment_status")
        assert status == "dispatched", (
            f"Expected ent_105 fulfillment_status='dispatched' but got "
            f"'{status}'."
        )


class TestEventOrdering:
    """Validates deterministic event ordering across streams."""

    def test_entity_event_count_with_fulfillment(self, snapshot_data):
        """Entity ent_101 must have 7 events (orders + payments + inventory + fulfillment).

        With all 4 streams loaded, ent_101 receives events from orders (2),
        payments (2), inventory (2), and fulfillment (1) = 7 total.
        """
        ent = get_entity(snapshot_data, "ent_101")
        assert ent is not None
        assert ent["event_count"] == 7, (
            f"Expected ent_101 event_count=7 but got {ent['event_count']}. "
            "This entity should receive events from all 4 streams."
        )

    def test_deterministic_ordering_at_timestamp_collision(self, snapshot_data):
        """Events at the same timestamp must be ordered by stream_id then sequence.

        At timestamp 1350, both stream_orders (ord_004, ent_102) and
        stream_payments (pay_002, ent_102) fire. With correct ordering
        (timestamp, stream_id, sequence), the orders event processes first
        because 'stream_orders' < 'stream_payments' lexicographically.
        Check the sort key in /app/runtime/sequencer.py — sequence numbers
        are local to each stream and cannot serve as a global tiebreaker.
        """
        ent = get_entity(snapshot_data, "ent_102")
        assert ent is not None
        # With correct ordering, ent_102 gets order event before payment at t=1350
        # Both provide different fields so the key check is event_count=6
        # (2 order + 1 payment + 2 inventory + 1 fulfillment)
        assert ent["event_count"] == 6, (
            f"Expected ent_102 event_count=6 but got {ent['event_count']}. "
            "Check that /app/runtime/sequencer.py sorts events by "
            "(timestamp, stream_id, sequence) for deterministic replay. "
            "Sequence numbers are local to each stream."
        )
