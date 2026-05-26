"""Validation tests for event projector output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
VIEW_PATH = os.path.join(OUTPUT_DIR, "materialized_view.json")
REPLAY_PATH = os.path.join(OUTPUT_DIR, "replay_sequence.json")


@pytest.fixture(scope="module")
def view_data():
    """Load materialized view output."""
    with open(VIEW_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def replay_data():
    """Load replay sequence output."""
    with open(REPLAY_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file validation — ensures system runs to completion."""

    def test_view_file_exists(self):
        """Materialized view output must be generated."""
        assert os.path.isfile(VIEW_PATH), (
            "materialized_view.json not found at /app/runtime/output/"
        )

    def test_replay_file_exists(self):
        """Replay sequence output must be generated."""
        assert os.path.isfile(REPLAY_PATH), (
            "replay_sequence.json not found at /app/runtime/output/"
        )

    def test_view_structure(self, view_data):
        """View output has required top-level fields."""
        assert "total_events_projected" in view_data
        assert "aggregate_count" in view_data
        assert "aggregates" in view_data
        assert "per_aggregate_counts" in view_data
        assert "snapshot_count" in view_data
        assert "snapshots" in view_data

    def test_replay_structure(self, replay_data):
        """Replay output has required top-level fields."""
        assert "total_events" in replay_data
        assert "replay_order" in replay_data
        assert "snapshot_interval" in replay_data


class TestAggregateLoading:
    """Validates that all configured aggregate types are loaded."""

    def test_total_events(self, view_data):
        """All 43 events from 4 aggregates must be projected.

        Four aggregate types are active: order (13), inventory (12),
        customer (10), shipping (8). Check /app/runtime/config.ini
        active_types list and ensure all types are matched correctly.
        """
        assert view_data["total_events_projected"] == 43, (
            f"Expected 43 total events from 4 aggregates, got "
            f"{view_data['total_events_projected']}. Check type matching "
            f"in /app/runtime/loader.py against config active_types."
        )

    def test_aggregate_count(self, view_data):
        """Must include all 4 aggregate types."""
        assert view_data["aggregate_count"] == 4, (
            f"Expected 4 aggregates, got {view_data['aggregate_count']}. "
            f"Check active_types parsing in /app/runtime/loader.py."
        )

    def test_shipping_aggregate_present(self, view_data):
        """Shipping aggregate must appear in aggregates list."""
        assert "shipping" in view_data["aggregates"], (
            "shipping aggregate missing. Check that the shipping type "
            "matches active_types config in /app/runtime/loader.py."
        )

    def test_all_aggregates_listed(self, view_data):
        """All 4 expected aggregates must be listed."""
        aggs = view_data["aggregates"]
        assert "customer" in aggs
        assert "inventory" in aggs
        assert "order" in aggs
        assert "shipping" in aggs


class TestSnapshotConfiguration:
    """Validates snapshot interval from correct config section."""

    def test_snapshot_interval(self, replay_data):
        """Snapshot interval must be 10 from projection.materialized section.

        The projector should read from the [projection.materialized]
        config section which has the production interval, not the
        [projection] section. Check /app/runtime/projector.py config
        section name.
        """
        assert replay_data["snapshot_interval"] == 10, (
            f"Expected snapshot_interval=10 from [projection.materialized], "
            f"got {replay_data['snapshot_interval']}. Check config section "
            f"in /app/runtime/projector.py — should read from "
            f"[projection.materialized] not [projection]."
        )

    def test_snapshot_count(self, view_data):
        """Must produce 5 snapshots (43 events / interval 10 = 5)."""
        assert view_data["snapshot_count"] == 5, (
            f"Expected 5 snapshots, got {view_data['snapshot_count']}."
        )


class TestProjectionState:
    """Validates per-interval snapshot state computation."""

    def test_first_snapshot_independent(self, view_data):
        """First snapshot state must contain only first 10 events.

        Each snapshot should reflect only events in that interval,
        not accumulate state from previous intervals. With interval=10,
        the first snapshot covers events 0-9.
        Check /app/runtime/projector.py for running totals that
        should be per-interval instead.
        """
        snapshots = view_data["snapshots"]
        first_state = snapshots[0]["state"]
        first_total = sum(first_state.values())
        assert first_total == 10, (
            f"First snapshot should contain exactly 10 events "
            f"(one interval), but has {first_total}. Snapshots "
            f"should reflect per-interval state, not cumulative. "
            f"Check /app/runtime/projector.py accumulation logic."
        )

    def test_shipping_in_per_aggregate_counts(self, view_data):
        """Shipping must have 8 events in per_aggregate_counts."""
        counts = view_data["per_aggregate_counts"]
        assert counts.get("shipping") == 8, (
            f"Expected shipping=8, got {counts.get('shipping')}."
        )

    def test_order_count(self, view_data):
        """Order aggregate must have 13 events."""
        counts = view_data["per_aggregate_counts"]
        assert counts.get("order") == 13

    def test_last_snapshot_remainder(self, view_data):
        """Last snapshot must cover remaining 3 events (43 mod 10)."""
        snapshots = view_data["snapshots"]
        last_state = snapshots[-1]["state"]
        last_total = sum(last_state.values())
        assert last_total == 3, (
            f"Last snapshot should have 3 events (43 mod 10), "
            f"got {last_total}."
        )


class TestReplayOrdering:
    """Validates deterministic event replay ordering."""

    def test_chronological_order(self, replay_data):
        """Events must be ordered by timestamp ascending."""
        events = replay_data["replay_order"]
        for i in range(1, len(events)):
            assert events[i]["timestamp"] >= events[i - 1]["timestamp"]

    def test_tiebreaker_at_timestamp_500(self, replay_data):
        """Events at timestamp 1700000500 must be ordered by aggregate_id.

        Four events share timestamp 1700000500 (inventory, order x2,
        shipping). Ordering must be deterministic using aggregate_id
        alphabetically then seq. Check sort key in
        /app/runtime/replayer.py — seq alone is not sufficient since
        seq is local to each aggregate.
        """
        events = replay_data["replay_order"]
        ts500 = [e for e in events if e["timestamp"] == 1700000500]
        assert len(ts500) == 4, (
            f"Expected 4 events at timestamp 1700000500, got {len(ts500)}. "
            f"All 4 aggregates must be loaded first."
        )
        agg_order = [e["aggregate_id"] for e in ts500]
        assert agg_order == ["inventory", "order", "order", "shipping"], (
            f"Events at ts=1700000500 should be ordered by aggregate_id: "
            f"inventory, order, order, shipping. Got {agg_order}. Check "
            f"sort key in /app/runtime/replayer.py — must include "
            f"aggregate_id for deterministic replay."
        )

    def test_total_replay_events(self, replay_data):
        """Replay sequence must contain all 43 events."""
        assert replay_data["total_events"] == 43
