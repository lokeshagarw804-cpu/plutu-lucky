"""Auditor — verifies Merkle inclusion proofs against the tree root.

Reconstructs the root hash from a leaf and its proof path, then
compares against the known root to determine validity. Also produces
a comprehensive audit report.
"""
import hashlib

from runtime.hasher import FIELD_SEPARATOR


def reconstruct_leaf_hash(transaction):
    """Recompute leaf hash from transaction fields for verification.

    Uses canonical field ordering: timestamp, account, txn_type, amount.
    Fields joined by the separator defined in hasher module.
    """
    canonical = "-".join([
        transaction["timestamp"],
        transaction["account"],
        transaction["txn_type"],
        transaction["amount"],
    ])
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_proof(leaf_hash, proof_steps, expected_root):
    """Walk the proof path from leaf to root and compare.

    For each step, concatenate current hash with sibling based on
    direction. Direction indicates where the SIBLING is:
    - "left": sibling is on the left → hash(sibling + current)
    - "right": sibling is on the right → hash(current + sibling)
    """
    current = leaf_hash

    for step in proof_steps:
        sibling = step["sibling_hash"]
        if step["direction"] == "left":
            combined = sibling + FIELD_SEPARATOR + current
        else:
            combined = current + FIELD_SEPARATOR + sibling
        current = hashlib.sha256(combined.encode("utf-8")).hexdigest()

    return current == expected_root


class Auditor:
    """Performs audit verification of transactions against Merkle root."""

    def __init__(self, tree_root, transactions, proofs):
        self._root = tree_root
        self._transactions = transactions
        self._proofs = proofs

    def run_audit(self):
        """Verify all proofs and produce audit report.

        Returns dict with verification results per transaction.
        """
        report = {
            "root_hash": self._root,
            "total_transactions": len(self._transactions),
            "verified_count": 0,
            "failed_count": 0,
            "results": [],
        }

        for idx_str, proof_steps in self._proofs.items():
            idx = int(idx_str)
            txn = self._transactions[idx]
            leaf_hash = reconstruct_leaf_hash(txn)
            verified = verify_proof(leaf_hash, proof_steps, self._root)

            result = {
                "txn_id": txn["txn_id"],
                "leaf_index": idx,
                "leaf_hash": leaf_hash,
                "verified": verified,
            }
            report["results"].append(result)

            if verified:
                report["verified_count"] += 1
            else:
                report["failed_count"] += 1

        report["audit_status"] = "pass" if report["failed_count"] == 0 else "fail"
        return report
