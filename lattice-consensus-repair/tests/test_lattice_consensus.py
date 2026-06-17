"""Validation tests for lattice consensus analyzer output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
FINALITY_MAP_PATH = os.path.join(OUTPUT_DIR, "finality_map.json")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "consensus_summary.json")


@pytest.fixture(scope="module")
def finality_map():
    """Load finality map output."""
    with open(FINALITY_MAP_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def summary():
    """Load consensus summary output."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file validation — verifies system ran and produced output."""

    def test_finality_map_exists(self):
        """Finality map output file must be generated at expected path."""
        assert os.path.isfile(FINALITY_MAP_PATH), (
            f"Expected output file at {FINALITY_MAP_PATH}"
        )

    def test_summary_exists(self):
        """Consensus summary output file must be generated at expected path."""
        assert os.path.isfile(SUMMARY_PATH), (
            f"Expected output file at {SUMMARY_PATH}"
        )

    def test_finality_map_is_list(self, finality_map):
        """Finality map must be a JSON array of transaction entries."""
        assert isinstance(finality_map, list)
        assert len(finality_map) > 0

    def test_summary_has_required_fields(self, summary):
        """Summary must contain all documented fields."""
        required = [
            "total_transactions", "total_finalized", "finality_rate",
            "total_validators", "validator_stats", "rounds_processed"
        ]
        for field in required:
            assert field in summary, f"Missing required field: {field}"


class TestValidatorLoading:
    """Validator loading — checks all configured validators are processed."""

    def test_total_validator_count(self, summary):
        """All 4 active validators must be loaded and processed.

        The active_validators config in /app/runtime/config.ini lists
        4 validators. Check that /app/runtime/loader.py correctly parses
        all entries from the comma-separated list.
        """
        assert summary["total_validators"] == 4, (
            f"Expected 4 validators but got {summary['total_validators']}. "
            "Verify that /app/runtime/loader.py correctly parses all entries "
            "from the active_validators configuration value."
        )

    def test_total_transaction_count(self, summary):
        """All 53 transactions from 4 validators must be in the DAG."""
        assert summary["total_transactions"] == 53, (
            f"Expected 53 transactions but got {summary['total_transactions']}. "
            "If validators are missing, their transactions won't appear."
        )

    def test_validator_4_present(self, summary):
        """Validator 4 must appear in per-validator statistics."""
        stats = summary["validator_stats"]
        assert "validator_4" in stats, (
            "validator_4 missing from stats. Check that the validator list "
            "parsing in /app/runtime/loader.py handles all list entries."
        )

    def test_validator_4_transaction_count(self, summary):
        """Validator 4 contributes 13 transactions to the DAG."""
        stats = summary["validator_stats"]
        if "validator_4" in stats:
            assert stats["validator_4"]["total_transactions"] == 13


class TestFinalityDecisions:
    """Finality checking — validates correct quorum threshold and depth."""

    def test_total_finalized_count(self, summary):
        """Exactly 12 transactions must achieve finality.

        Finality requires normalized_weight >= quorum_threshold from the
        consensus.finality config section and sufficient confirmation depth.
        """
        assert summary["total_finalized"] == 12, (
            f"Expected 12 finalized but got {summary['total_finalized']}. "
            "Check which config section /app/runtime/finality_checker.py "
            "reads quorum_threshold from — it should use consensus.finality "
            "(quorum_threshold=0.67), not consensus (quorum_threshold=0.80)."
        )

    def test_finality_rate(self, summary):
        """Overall finality rate must be approximately 0.2264."""
        rate = summary["finality_rate"]
        assert abs(rate - 0.2264) < 0.01, (
            f"Expected finality_rate ~0.2264 but got {rate}"
        )

    def test_validator_1_finalized(self, summary):
        """Validator 1 should have exactly 5 finalized transactions."""
        stats = summary["validator_stats"]
        v1 = stats.get("validator_1", {})
        assert v1.get("finalized_count") == 5, (
            f"Expected validator_1 to have 5 finalized, got "
            f"{v1.get('finalized_count')}"
        )

    def test_validator_2_finalized(self, summary):
        """Validator 2 should have exactly 5 finalized transactions."""
        stats = summary["validator_stats"]
        v2 = stats.get("validator_2", {})
        assert v2.get("finalized_count") == 5, (
            f"Expected validator_2 to have 5 finalized, got "
            f"{v2.get('finalized_count')}"
        )

    def test_validator_3_finalized(self, summary):
        """Validator 3 should have exactly 2 finalized transactions."""
        stats = summary["validator_stats"]
        v3 = stats.get("validator_3", {})
        assert v3.get("finalized_count") == 2, (
            f"Expected validator_3 to have 2 finalized, got "
            f"{v3.get('finalized_count')}"
        )


class TestCausalOrdering:
    """DAG ordering — validates deterministic causal sort of transactions."""

    def test_finality_map_size(self, finality_map):
        """Finality map must contain all 53 transactions."""
        assert len(finality_map) == 53

    def test_timestamp_ordering(self, finality_map):
        """Transactions must be non-decreasing by timestamp."""
        timestamps = [entry["timestamp"] for entry in finality_map]
        assert timestamps == sorted(timestamps), (
            "Finality map entries must be sorted by timestamp"
        )

    def test_deterministic_tiebreak(self, finality_map):
        """Same-timestamp entries must be ordered by validator_id then seq.

        When multiple validators issue transactions at the same timestamp,
        the sort must use validator_id as secondary key for deterministic
        ordering. Check the sort key in /app/runtime/dag_builder.py —
        seq alone is not sufficient because it is local to each validator.
        """
        # Check entries at timestamp 1000 (3 validators issue at same time)
        ts1000 = [e for e in finality_map if e["timestamp"] == 1000]
        if len(ts1000) >= 3:
            vids = [e["validator_id"] for e in ts1000]
            assert vids == sorted(vids), (
                f"At timestamp 1000, expected validators in order "
                f"{sorted(vids)} but got {vids}. "
                "The sort in /app/runtime/dag_builder.py needs validator_id "
                "as tiebreaker — seq is local to each validator."
            )

    def test_timestamp_1003_order(self, finality_map):
        """Entries at timestamp 1003 must follow deterministic ordering."""
        ts1003 = [e for e in finality_map if e["timestamp"] == 1003]
        if len(ts1003) >= 4:
            vids = [e["validator_id"] for e in ts1003]
            expected = ["validator_1", "validator_2", "validator_3", "validator_4"]
            assert vids == expected, (
                f"At timestamp 1003, expected validator order {expected} "
                f"but got {vids}"
            )
