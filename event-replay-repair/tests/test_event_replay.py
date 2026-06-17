"""Validation tests for CQRS event replay engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
PROJECTION_PATH = os.path.join(OUTPUT_DIR, "projection_state.json")
SNAPSHOTS_PATH = os.path.join(OUTPUT_DIR, "snapshots.json")
RECONCILIATION_PATH = os.path.join(OUTPUT_DIR, "reconciliation.json")


@pytest.fixture(scope="module")
def projection_data():
    """Load projection state output."""
    with open(PROJECTION_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def snapshots_data():
    """Load snapshots output."""
    with open(SNAPSHOTS_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def reconciliation_data():
    """Load reconciliation output."""
    with open(RECONCILIATION_PATH, "r") as f:
        return json.load(f)


class TestOutputFileStructure:
    """Basic output file existence and structure validation."""

    def test_projection_file_exists(self):
        """Projection state output file must be generated."""
        assert os.path.isfile(PROJECTION_PATH)

    def test_snapshots_file_exists(self):
        """Snapshots output file must be generated."""
        assert os.path.isfile(SNAPSHOTS_PATH)

    def test_reconciliation_file_exists(self):
        """Reconciliation output file must be generated."""
        assert os.path.isfile(RECONCILIATION_PATH)

    def test_projection_structure(self, projection_data):
        """Projection output must contain required fields."""
        assert "total_events_processed" in projection_data
        assert "total_accounts" in projection_data
        assert "balances" in projection_data
        assert "streams_loaded" in projection_data


class TestStreamLoading:
    """Validates that all configured streams are loaded correctly."""

    def test_all_streams_loaded(self, projection_data):
        """All 4 configured streams must be loaded including refunds."""
        loaded = projection_data["streams_loaded"]
        assert len(loaded) == 4, (
            f"Expected 4 streams but got {len(loaded)}: {loaded}. "
            f"Check stream filtering in /app/runtime/stream_loader.py — "
            f"verify how included_streams config value is parsed."
        )

    def test_refunds_stream_present(self, projection_data):
        """The refunds stream must be included in loaded streams."""
        loaded = projection_data["streams_loaded"]
        assert "refunds" in loaded, (
            f"Stream 'refunds' missing from loaded streams: {loaded}. "
            f"Check how /app/runtime/stream_loader.py splits the "
            f"included_streams configuration value."
        )

    def test_total_event_count(self, projection_data):
        """Must process exactly 50 events from all 4 streams."""
        assert projection_data["total_events_processed"] == 50, (
            f"Expected 50 events but processed "
            f"{projection_data['total_events_processed']}. "
            f"Missing events likely from a stream not being loaded."
        )


class TestProjectionBalances:
    """Validates final projected account balances."""

    def test_account_count(self, projection_data):
        """Must have exactly 3 unique accounts."""
        assert projection_data["total_accounts"] == 3

    def test_acct_100_balance(self, projection_data):
        """Account 100 final balance must reflect all credits and debits."""
        bal = projection_data["balances"]["acct_100"]
        assert abs(bal - 986.20) < 0.01, (
            f"acct_100 balance is {bal}, expected ~986.20. "
            f"This requires all streams including refunds to be loaded "
            f"and events ordered deterministically."
        )

    def test_acct_101_balance(self, projection_data):
        """Account 101 final balance depends on correct event ordering."""
        bal = projection_data["balances"]["acct_101"]
        assert abs(bal - 1064.93) < 0.01, (
            f"acct_101 balance is {bal}, expected ~1064.93. "
            f"Check sequencer ordering — events at same timestamp from "
            f"different streams need stable sort by stream_id then sequence_num."
        )

    def test_acct_102_balance(self, projection_data):
        """Account 102 final balance validates complete event processing."""
        bal = projection_data["balances"]["acct_102"]
        assert abs(bal - 468.15) < 0.01, (
            f"acct_102 balance is {bal}, expected ~468.15."
        )


class TestSnapshotIntegrity:
    """Validates periodic snapshot checkpoint correctness."""

    def test_snapshot_count(self, snapshots_data):
        """Must produce exactly 5 snapshots (50 events / 10 interval)."""
        assert snapshots_data["total_snapshots"] == 5, (
            f"Expected 5 snapshots but got {snapshots_data['total_snapshots']}. "
            f"With 50 events and interval=10, there should be 5 checkpoints."
        )

    def test_snapshot_balances_not_inflated(self, snapshots_data):
        """Snapshot balances must not grow disproportionately across checkpoints."""
        snaps = snapshots_data["snapshots"]
        if len(snaps) >= 2:
            first_total = sum(snaps[0]["balances"].values())
            last_total = sum(snaps[-1]["balances"].values())
            # Last snapshot total should be reasonable (not accumulated across snapshots)
            assert last_total < 5000.0, (
                f"Last snapshot total balance is {last_total}, which is "
                f"unreasonably high. Check /app/runtime/snapshot_builder.py — "
                f"snapshots should record point-in-time balances, not "
                f"accumulate across checkpoints."
            )

    def test_final_snapshot_matches_projection(self, snapshots_data, projection_data):
        """Last snapshot must equal final projected balances (same event set)."""
        snaps = snapshots_data["snapshots"]
        last_snap = snaps[-1]
        proj_balances = projection_data["balances"]
        for acct, proj_bal in proj_balances.items():
            snap_bal = last_snap["balances"].get(acct, 0.0)
            assert abs(proj_bal - snap_bal) < 0.01, (
                f"Account {acct}: projection={proj_bal}, last_snapshot={snap_bal}. "
                f"Final snapshot should match projected state since both "
                f"process the same 50 events."
            )


class TestReconciliation:
    """Validates audit reconciliation correctness."""

    def test_reconciliation_status_clean(self, reconciliation_data):
        """Reconciliation must report clean status with no discrepancies."""
        assert reconciliation_data["status"] == "clean", (
            f"Reconciliation status is '{reconciliation_data['status']}', "
            f"expected 'clean'. Check rounding precision in "
            f"/app/runtime/reconciler.py — the reconciliation section "
            f"in config.ini specifies the correct decimal_places to use."
        )

    def test_no_discrepancies(self, reconciliation_data):
        """Discrepancy list must be empty when all bugs are fixed."""
        discs = reconciliation_data["discrepancies"]
        assert len(discs) == 0, (
            f"Found {len(discs)} discrepancies: "
            f"{[d['account_id'] for d in discs]}. "
            f"Verify that snapshot_builder captures point-in-time balances "
            f"and reconciler uses [projection.reconciliation] decimal_places."
        )

    def test_all_accounts_reconciled(self, reconciliation_data):
        """All accounts must be successfully reconciled."""
        assert reconciliation_data["reconciled_accounts"] == 3, (
            f"Only {reconciliation_data['reconciled_accounts']}/3 accounts "
            f"reconciled. Check reconciliation decimal precision."
        )
