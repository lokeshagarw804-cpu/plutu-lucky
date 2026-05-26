"""
Tests for the event replay projection system.

Validates correctness of event filtering, batch windowing,
projection building, and deterministic event ordering.
"""
import json
import os
import pytest


EVENT_LOG_PATH = "/app/runtime/output/event_log.json"
SUMMARY_PATH = "/app/runtime/output/replay_summary.json"


def load_event_log():
    """Load the event processing log output file."""
    with open(EVENT_LOG_PATH, "r") as f:
        return json.load(f)


def load_summary():
    """Load the replay summary output file."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


# --- EASY TESTS (pass even with buggy code) ---

class TestOutputFileStructure:
    """Tests that verify basic output file existence and structure."""

    def test_event_log_exists(self):
        """The event log output file must exist at the configured path."""
        assert os.path.isfile(EVENT_LOG_PATH), (
            f"Expected event log at {EVENT_LOG_PATH}"
        )

    def test_summary_exists(self):
        """The replay summary output file must exist at the configured path."""
        assert os.path.isfile(SUMMARY_PATH), (
            f"Expected replay summary at {SUMMARY_PATH}"
        )

    def test_event_log_has_required_fields(self):
        """The event log must contain all required top-level fields."""
        log = load_event_log()
        required = ["total_events", "entries"]
        for field in required:
            assert field in log, (
                f"Missing required field '{field}' in event log"
            )

    def test_summary_has_required_fields(self):
        """The replay summary must contain all required top-level fields."""
        summary = load_summary()
        required = [
            "total_events_processed", "total_batches", "stream_counts",
            "type_counts", "total_entities", "entity_states", "batch_totals"
        ]
        for field in required:
            assert field in summary, (
                f"Missing required field '{field}' in replay summary"
            )


# --- MEDIUM TESTS (require 1-2 bug fixes each) ---

class TestEventFiltering:
    """Tests for event type filtering correctness."""

    def test_total_event_count(self):
        """All 43 events from 3 stream files must be processed.

        The system has 3 source streams with 17 + 13 + 13 = 43 events.
        If fewer events appear, check how the event type filter parses the
        allowed types list in /app/runtime/filter.py.
        """
        log = load_event_log()
        assert log["total_events"] == 43, (
            f"Expected 43 total events, got {log['total_events']}. "
            "Check how event_types config value is parsed in "
            "/app/runtime/filter.py — whitespace in the comma-separated "
            "list may cause types to be silently excluded."
        )

    def test_stock_adjusted_events_included(self):
        """Events of type stock_adjusted must pass the filter.

        The stock_adjusted type is configured in the allowed event_types list.
        If these events are missing, check config parsing in /app/runtime/filter.py.
        """
        log = load_event_log()
        entries = log["entries"]
        adjusted_events = [
            e for e in entries if e["event_type"] == "stock_adjusted"
        ]
        assert len(adjusted_events) == 3, (
            f"Expected 3 stock_adjusted events, got {len(adjusted_events)}. "
            "The stock_adjusted type is in the config but may not match due "
            "to whitespace. Check /app/runtime/filter.py parsing logic."
        )

    def test_all_event_types_present(self):
        """All 9 configured event types must appear in the processed output."""
        log = load_event_log()
        entries = log["entries"]
        types_seen = set(e["event_type"] for e in entries)
        expected_types = {
            "order_placed", "order_confirmed", "order_shipped",
            "payment_initiated", "payment_completed", "payment_refunded",
            "stock_reserved", "stock_released", "stock_adjusted"
        }
        missing = expected_types - types_seen
        assert not missing, (
            f"Missing event types in output: {missing}. "
            "Check config parsing in /app/runtime/filter.py."
        )


# --- MEDIUM-HARD TESTS (require 2-3 bug fixes) ---

class TestBatchWindowing:
    """Tests for batch window size and count."""

    def test_batch_count(self):
        """Events spanning 4 days with 24-hour windows should produce 4 batches.

        The replay.streaming section in /app/runtime/config.ini specifies
        batch_window_hours=24. Check that /app/runtime/projector.py reads
        from the correct config section.
        """
        summary = load_summary()
        assert summary["total_batches"] == 4, (
            f"Expected 4 batches with 24-hour window, got "
            f"{summary['total_batches']}. Check which config section "
            "/app/runtime/projector.py reads batch_window_hours from — "
            "it should use replay.streaming (24h), not replay (48h)."
        )

    def test_batch_totals_reflect_last_window_only(self):
        """Batch totals must reflect only the final window, not accumulated values.

        With snapshot_mode=latest, the batch_totals should contain counts
        from only the most recent batch window. If totals seem too high,
        check whether /app/runtime/projector.py resets batch_totals between
        windows.
        """
        summary = load_summary()
        batch_totals = summary["batch_totals"]
        total_in_batch = sum(
            v["event_count"] for v in batch_totals.values()
        )
        assert total_in_batch < summary["total_events_processed"], (
            f"batch_totals event_count sum ({total_in_batch}) equals "
            f"total_events_processed ({summary['total_events_processed']}). "
            "This means totals accumulated across ALL windows instead of "
            "reflecting only the last window. Check /app/runtime/projector.py "
            "— batch_totals should reset at the start of each new window."
        )

    def test_batch_totals_event_count_matches_last_batch(self):
        """The final batch window should have exactly 2 events.

        With correct 24-hour windowing and all events included, the last
        batch contains events from 2024-01-18T16:00:00Z only (2 events).
        """
        summary = load_summary()
        batch_totals = summary["batch_totals"]
        total_in_final = sum(
            v["event_count"] for v in batch_totals.values()
        )
        assert total_in_final == 2, (
            f"Expected 2 events in final batch window, got {total_in_final}. "
            "This requires both correct window size (24h from replay.streaming) "
            "and proper reset of batch_totals between windows in "
            "/app/runtime/projector.py."
        )


# --- HARD TESTS (require 3-4 bug fixes together) ---

class TestDeterministicOrdering:
    """Tests for deterministic event replay ordering."""

    def test_event_order_at_collision_timestamp(self):
        """Events at 2024-01-17T09:00:00Z must be ordered by stream_id.

        At this timestamp, events exist from both orders (seq=12) and
        payments (seq=10). Sorting by sequence alone puts payments first
        (seq 10 < 12), but correct order is orders first since
        'orders' < 'payments' alphabetically. Check the sort key in
        /app/runtime/sorter.py — must sort by (timestamp, stream_id, sequence)
        not just (timestamp, sequence).
        """
        log = load_event_log()
        entries = log["entries"]
        collision_events = [
            e for e in entries if e["timestamp"] == "2024-01-17T09:00:00Z"
        ]
        assert len(collision_events) >= 2, (
            "Expected at least 2 events at 2024-01-17T09:00:00Z"
        )
        stream_order = [e["stream_id"] for e in collision_events]
        assert stream_order == sorted(stream_order), (
            f"Events at 2024-01-17T09:00:00Z have wrong order: {stream_order}. "
            f"Expected alphabetical stream order. Check sort key in "
            f"/app/runtime/sorter.py — must include stream_id."
        )

    def test_three_way_collision_ordering(self):
        """Events at 2024-01-17T14:00:00Z from 3 streams must be correctly ordered.

        Three events from inventory(seq=10), orders(seq=14), and payments(seq=11)
        share this timestamp. Correct order by (timestamp, stream_id, sequence):
        inventory, orders, payments. Buggy order by (timestamp, sequence):
        inventory(10), payments(11), orders(14).
        """
        log = load_event_log()
        entries = log["entries"]
        collision_events = [
            e for e in entries if e["timestamp"] == "2024-01-17T14:00:00Z"
        ]
        assert len(collision_events) == 3, (
            f"Expected 3 events at 2024-01-17T14:00:00Z, got "
            f"{len(collision_events)}. All event types must pass the filter."
        )
        stream_order = [e["stream_id"] for e in collision_events]
        expected_order = ["inventory", "orders", "payments"]
        assert stream_order == expected_order, (
            f"Events at 2024-01-17T14:00:00Z have wrong order: {stream_order}. "
            f"Expected {expected_order}. Check sort key in "
            f"/app/runtime/sorter.py — sequence is local to each stream."
        )

    def test_overall_event_sequence_deterministic(self):
        """The full event log must maintain stable ordering throughout.

        Every pair of adjacent events must satisfy:
        (timestamp_i, stream_id_i, sequence_i) <= (timestamp_j, stream_id_j, sequence_j)
        """
        log = load_event_log()
        entries = log["entries"]
        for i in range(len(entries) - 1):
            curr = entries[i]
            nxt = entries[i + 1]
            curr_key = (curr["timestamp"], curr["stream_id"], curr["sequence"])
            nxt_key = (nxt["timestamp"], nxt["stream_id"], nxt["sequence"])
            assert curr_key <= nxt_key, (
                f"Event log not sorted correctly at position {i}: "
                f"{curr['event_id']} ({curr_key}) should come before "
                f"{nxt['event_id']} ({nxt_key}). "
                f"Check sort key in /app/runtime/sorter.py — must sort by "
                f"(timestamp, stream_id, sequence) not just (timestamp, sequence)."
            )
