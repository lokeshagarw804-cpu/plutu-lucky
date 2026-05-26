"""Merkle proof verification and audit reporting.

Provides independent verification of inclusion proofs against a known
Merkle root. The verifier reconstructs the root from a leaf hash and
proof path, then compares against the expected value.
"""
import hashlib


def reconstruct_leaf_hash(transaction):
    """Reconstruct the leaf hash for a transaction during verification.

    Computes the same canonical hash that was used during tree construction,
    allowing the verifier to independently derive the starting point for
    proof traversal.

    Args:
        transaction: dict with keys tx_id, account, amount, currency

    Returns:
        Hex-encoded SHA-256 digest of the canonical transaction string.
    """
    canonical = (
        f"{transaction['tx_id']}:"
        f"{transaction['account']}:"
        f"{transaction['amount']}:"
        f"{transaction['currency']}"
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _compute_parent_hash(left_hash, right_hash):
    """Compute parent hash from two children during proof verification.

    Concatenates the child hashes and applies SHA-256 to produce the
    parent digest. This must match the node hash computation used
    during tree construction.

    Args:
        left_hash: hex digest of the left child
        right_hash: hex digest of the right child

    Returns:
        Hex-encoded SHA-256 of the concatenated children.
    """
    data = f"{left_hash}{right_hash}"
    return hashlib.sha256(data.encode()).hexdigest()


def verify_proof(leaf_hash, proof_path, expected_root):
    """Verify a Merkle inclusion proof against an expected root.

    Walks the proof path from leaf to root, combining the current hash
    with each sibling according to the specified direction, then checks
    if the final computed root matches the expected value.

    Args:
        leaf_hash: hex digest of the leaf being verified
        proof_path: list of proof steps with hash and direction
        expected_root: hex digest of the expected Merkle root

    Returns:
        Boolean indicating whether the proof is valid.
    """
    current = leaf_hash

    for step in proof_path:
        if step["direction"] == "left":
            current = _compute_parent_hash(step["hash"], current)
        else:
            current = _compute_parent_hash(current, step["hash"])

    return current == expected_root


def run_audit(transactions, proofs, expected_root):
    """Run full audit verification on all transaction proofs.

    For each transaction, independently reconstructs the leaf hash and
    verifies the inclusion proof against the expected root.

    Args:
        transactions: list of transaction dicts
        proofs: dict mapping tx_id to proof data
        expected_root: the Merkle root to verify against

    Returns:
        dict with verification summary:
            - total_proofs: number of proofs checked
            - valid_count: number that verified successfully
            - invalid_count: number that failed verification
            - results: dict mapping tx_id to boolean result
    """
    results = {}
    valid_count = 0
    invalid_count = 0

    for tx in transactions:
        tx_id = tx["tx_id"]
        if tx_id not in proofs:
            results[tx_id] = False
            invalid_count += 1
            continue

        proof_data = proofs[tx_id]
        leaf_hash = reconstruct_leaf_hash(tx)
        is_valid = verify_proof(leaf_hash, proof_data["proof_path"], expected_root)

        results[tx_id] = is_valid
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

    return {
        "total_proofs": len(transactions),
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "results": results,
    }
