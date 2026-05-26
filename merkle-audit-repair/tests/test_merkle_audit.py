"""Test suite for Merkle audit verification system.

Validates tree construction, proof generation, and verification
against known-correct reference values.
"""
import json
import os
import pytest


AUDIT_OUTPUT = "/app/runtime/output/audit_result.json"

EXPECTED_ROOT = "d8a88a3a24ce283e4e8c7ca6ba20b67a99ad8e5ed4ed2694d945341c5c843926"
EXPECTED_LEAF_COUNT = 11
EXPECTED_DEPTH = 5
EXPECTED_LEVEL_SIZES = [11, 6, 3, 2, 1]
EXPECTED_PROOF_COUNT = 11

FIRST_LEAF_HASH = "b04c38e0973c5d8f4fac373c82eea9724489eaaa7bbe442f80ac271fe9cb8e27"
LAST_LEAF_HASH = "aacaf3f9698c17c5604a6cad1f707a1317f803ceb58e502e4d09fd3fa0699c95"


@pytest.fixture
def audit_result():
    """Load the audit result output."""
    assert os.path.exists(AUDIT_OUTPUT), f"Output file not found: {AUDIT_OUTPUT}"
    with open(AUDIT_OUTPUT, "r") as f:
        return json.load(f)


# === BASIC STRUCTURAL TESTS (4 tests) ===


class TestStructure:
    """Basic structural validation tests."""

    def test_output_file_exists(self):
        """Output file should be created."""
        assert os.path.exists(AUDIT_OUTPUT)

    def test_output_has_required_keys(self, audit_result):
        """Output should contain tree, proofs, and verification sections."""
        assert "tree" in audit_result
        assert "proofs" in audit_result
        assert "verification" in audit_result

    def test_tree_has_required_fields(self, audit_result):
        """Tree section should have root_hash, leaf_count, depth, level_sizes."""
        tree = audit_result["tree"]
        assert "root_hash" in tree
        assert "leaf_count" in tree
        assert "depth" in tree
        assert "level_sizes" in tree

    def test_verification_has_required_fields(self, audit_result):
        """Verification section should have counts and results."""
        v = audit_result["verification"]
        assert "total_proofs" in v
        assert "valid_count" in v
        assert "invalid_count" in v
        assert "results" in v


# === MEDIUM TESTS (3 tests) ===


class TestTreeMetrics:
    """Tree construction metric validation."""

    def test_leaf_count(self, audit_result):
        """Tree should contain exactly 11 transaction leaves."""
        assert audit_result["tree"]["leaf_count"] == EXPECTED_LEAF_COUNT

    def test_tree_depth(self, audit_result):
        """Tree depth should be 5 levels (leaves through root)."""
        assert audit_result["tree"]["depth"] == EXPECTED_DEPTH

    def test_proof_count(self, audit_result):
        """Should generate one proof per transaction."""
        assert len(audit_result["proofs"]) == EXPECTED_PROOF_COUNT


# === HARD TESTS: Tree correctness (4 tests) ===


class TestTreeCorrectness:
    """Validates the computed tree matches reference values."""

    def test_root_hash(self, audit_result):
        """Root hash must match the expected reference value."""
        assert audit_result["tree"]["root_hash"] == EXPECTED_ROOT

    def test_level_sizes(self, audit_result):
        """Level sizes should reflect correct tree shape with padding."""
        assert audit_result["tree"]["level_sizes"] == EXPECTED_LEVEL_SIZES

    def test_first_leaf_hash(self, audit_result):
        """First leaf hash must match TX-0001 reference value."""
        proofs = audit_result["proofs"]
        assert proofs["TX-0001"]["leaf_hash"] == FIRST_LEAF_HASH

    def test_last_leaf_hash(self, audit_result):
        """Last leaf hash must match TX-0011 reference value."""
        proofs = audit_result["proofs"]
        assert proofs["TX-0011"]["leaf_hash"] == LAST_LEAF_HASH


# === HARD TESTS: Proof structure (3 tests) ===


class TestProofStructure:
    """Validates proof generation correctness."""

    def test_proof_path_length(self, audit_result):
        """All proofs should have path length equal to depth - 1."""
        expected_length = EXPECTED_DEPTH - 1
        for tx_id, proof_data in audit_result["proofs"].items():
            assert len(proof_data["proof_path"]) == expected_length, (
                f"Proof for {tx_id} has length {len(proof_data['proof_path'])}, "
                f"expected {expected_length}"
            )

    def test_leaf_ordering_tx0001_first(self, audit_result):
        """TX-0001 should be at leaf index 0 (from ledger_1, first file numerically)."""
        assert audit_result["proofs"]["TX-0001"]["leaf_index"] == 0

    def test_leaf_ordering_tx0008_at_seven(self, audit_result):
        """TX-0008 should be at leaf index 7 (from ledger_10, third file numerically)."""
        assert audit_result["proofs"]["TX-0008"]["leaf_index"] == 7


# === HARD TESTS: Verification (5 tests) ===


class TestVerification:
    """Validates proof verification correctness."""

    def test_all_proofs_valid(self, audit_result):
        """All 11 proofs should verify successfully."""
        v = audit_result["verification"]
        assert v["valid_count"] == EXPECTED_LEAF_COUNT
        assert v["invalid_count"] == 0

    def test_no_invalid_results(self, audit_result):
        """Every individual result should be True."""
        results = audit_result["verification"]["results"]
        for tx_id, is_valid in results.items():
            assert is_valid is True, f"Verification failed for {tx_id}"

    def test_verification_tx0002_valid(self, audit_result):
        """TX-0002 (odd index 1) proof must verify — exercises parent indexing."""
        results = audit_result["verification"]["results"]
        assert results["TX-0002"] is True

    def test_verification_tx0005_valid(self, audit_result):
        """TX-0005 (first in ledger_2, index 4) proof must verify."""
        results = audit_result["verification"]["results"]
        assert results["TX-0005"] is True

    def test_verification_tx0011_valid(self, audit_result):
        """TX-0011 (last leaf, padded sibling) proof must verify."""
        results = audit_result["verification"]["results"]
        assert results["TX-0011"] is True
