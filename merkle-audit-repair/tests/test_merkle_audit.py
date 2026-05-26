"""Validation tests for Merkle audit verification system."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
TREE_PATH = os.path.join(OUTPUT_DIR, "tree_state.json")
PROOFS_PATH = os.path.join(OUTPUT_DIR, "proofs.json")
AUDIT_PATH = os.path.join(OUTPUT_DIR, "audit_report.json")


@pytest.fixture(scope="module")
def tree_data():
    """Load tree state output."""
    with open(TREE_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def proofs_data():
    """Load proofs output."""
    with open(PROOFS_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def audit_data():
    """Load audit report output."""
    with open(AUDIT_PATH, "r") as f:
        return json.load(f)


class TestOutputFileStructure:
    """Basic output file existence and structure checks."""

    def test_tree_state_file_exists(self):
        """Tree state output file must be generated."""
        assert os.path.isfile(TREE_PATH)

    def test_proofs_file_exists(self):
        """Proofs output file must be generated."""
        assert os.path.isfile(PROOFS_PATH)

    def test_audit_report_file_exists(self):
        """Audit report output file must be generated."""
        assert os.path.isfile(AUDIT_PATH)

    def test_tree_state_structure(self, tree_data):
        """Tree state must contain required fields."""
        assert "leaf_count" in tree_data
        assert "tree_depth" in tree_data
        assert "root_hash" in tree_data
        assert "leaf_hashes" in tree_data


class TestTreeConstruction:
    """Validates Merkle tree structure properties."""

    def test_leaf_count(self, tree_data):
        """Must have exactly 7 leaves from the two ledger files."""
        assert tree_data["leaf_count"] == 7

    def test_tree_depth(self, tree_data):
        """Tree with 7 leaves must have depth 4 (8,4,2,1 padded levels)."""
        assert tree_data["tree_depth"] == 4, (
            f"Expected depth 4 but got {tree_data['tree_depth']}. "
            f"Check padding logic in /app/runtime/tree_builder.py."
        )

    def test_leaf_hashes_are_valid_sha256(self, tree_data):
        """All leaf hashes must be 64-character hex strings (SHA-256)."""
        for h in tree_data["leaf_hashes"]:
            assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)

    def test_root_hash_is_valid_sha256(self, tree_data):
        """Root hash must be a valid SHA-256 hex string."""
        root = tree_data["root_hash"]
        assert len(root) == 64 and all(c in "0123456789abcdef" for c in root)

    def test_leaf_hashes_count_matches(self, tree_data):
        """Number of leaf hashes must match leaf_count."""
        assert len(tree_data["leaf_hashes"]) == tree_data["leaf_count"]


class TestProofGeneration:
    """Validates inclusion proof structure."""

    def test_proof_count(self, proofs_data):
        """Must generate a proof for each of the 7 transactions."""
        assert proofs_data["total_proofs"] == 7

    def test_proof_depth(self, proofs_data):
        """Each proof must have exactly 3 steps (depth-1 for 4-level tree)."""
        for idx_str, steps in proofs_data["proofs"].items():
            assert len(steps) == 3, (
                f"Proof for leaf {idx_str} has {len(steps)} steps, "
                f"expected 3 for a tree of depth 4."
            )

    def test_proof_directions_valid(self, proofs_data):
        """All proof step directions must be 'left' or 'right'."""
        for idx_str, steps in proofs_data["proofs"].items():
            for step in steps:
                assert step["direction"] in ("left", "right"), (
                    f"Invalid direction '{step['direction']}' in proof "
                    f"for leaf {idx_str}."
                )

    def test_proof_sibling_hashes_are_sha256(self, proofs_data):
        """All sibling hashes in proofs must be valid SHA-256."""
        for idx_str, steps in proofs_data["proofs"].items():
            for step in steps:
                h = step["sibling_hash"]
                assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)


class TestAuditVerification:
    """Validates audit verification results — requires all bugs fixed."""

    def test_audit_status_pass(self, audit_data):
        """Audit must report status 'pass' when all proofs verify."""
        assert audit_data["audit_status"] == "pass", (
            f"Audit status is '{audit_data['audit_status']}', expected 'pass'. "
            f"Verification failed — check that hasher and auditor use the same "
            f"field order and separator for leaf hash computation, that "
            f"tree_builder pads odd levels correctly, and that proof_engine "
            f"direction flags are consistent with auditor's reconstruction."
        )

    def test_verified_count(self, audit_data):
        """All 7 transactions must verify successfully."""
        assert audit_data["verified_count"] == 7, (
            f"Only {audit_data['verified_count']}/7 verified. "
            f"The tree construction, proof generation, and verification "
            f"modules must agree on their conventions."
        )

    def test_no_failures(self, audit_data):
        """No transactions should fail verification."""
        assert audit_data["failed_count"] == 0, (
            f"{audit_data['failed_count']} transactions failed verification."
        )

    def test_all_results_verified(self, audit_data):
        """Each individual result must show verified=true."""
        for result in audit_data["results"]:
            assert result["verified"] is True, (
                f"Transaction {result['txn_id']} at index {result['leaf_index']} "
                f"failed verification. Its leaf_hash was {result['leaf_hash'][:16]}..."
            )

    def test_result_count_matches(self, audit_data):
        """Must have a result entry for each transaction."""
        assert len(audit_data["results"]) == 7

    def test_leaf_hash_consistency(self, tree_data, audit_data):
        """Auditor's recomputed leaf hashes must match tree leaf hashes."""
        tree_leaves = tree_data["leaf_hashes"]
        for result in audit_data["results"]:
            idx = result["leaf_index"]
            assert result["leaf_hash"] == tree_leaves[idx], (
                f"Leaf hash mismatch at index {idx}: "
                f"tree={tree_leaves[idx][:16]}... vs "
                f"audit={result['leaf_hash'][:16]}... "
                f"Check that /app/runtime/auditor.py reconstructs leaf hashes "
                f"using the same field order and separator as /app/runtime/hasher.py."
            )
