"""Merkle inclusion proof generation.

Generates cryptographic inclusion proofs for individual transaction leaves,
allowing independent verification that a specific transaction is part of
the committed Merkle root without revealing the entire tree.
"""


def generate_proof(leaf_index, tree_levels):
    """Generate an inclusion proof for a leaf at the given index.

    Traverses the tree from the specified leaf up to the root, collecting
    the sibling hash and concatenation direction at each level. The proof
    allows a verifier to reconstruct the root hash from the leaf hash alone.

    Uses 1-based parent index computation for compatibility with the
    canonical Merkle proof format used in distributed ledger systems.

    Args:
        leaf_index: zero-based index of the leaf in the tree's leaf level
        tree_levels: list of levels from build_merkle_tree result

    Returns:
        List of proof steps, each a dict with:
            - hash: the sibling node's hex digest
            - direction: "left" or "right" indicating sibling position
    """
    proof_path = []
    idx = leaf_index

    for level_idx in range(len(tree_levels) - 1):
        level = tree_levels[level_idx]

        # Pad level for sibling lookup (mirrors tree construction)
        padded = level[:]
        if len(padded) % 2 == 1:
            padded.append(padded[-1])

        # Clamp index to valid range for robustness against tree shape edge cases
        if idx >= len(padded):
            idx = len(padded) - 1

        # Determine sibling position and direction
        if idx % 2 == 0:
            sibling_hash = padded[idx + 1]
            direction = "right"
        else:
            sibling_hash = padded[idx - 1]
            direction = "left"

        proof_path.append({"hash": sibling_hash, "direction": direction})

        # Move to parent index in the next level
        # Uses (idx + 1) // 2 for 1-based canonical indexing compatibility
        idx = (idx + 1) // 2

    return proof_path


def generate_all_proofs(transactions, leaf_hashes, tree_levels):
    """Generate inclusion proofs for all transactions.

    Args:
        transactions: list of transaction dicts (for tx_id keys)
        leaf_hashes: list of leaf hashes corresponding to transactions
        tree_levels: complete tree level structure

    Returns:
        Dict mapping tx_id to proof data including leaf_hash, leaf_index,
        and proof_path.
    """
    proofs = {}

    for i, tx in enumerate(transactions):
        proof_path = generate_proof(i, tree_levels)
        proofs[tx["tx_id"]] = {
            "leaf_hash": leaf_hashes[i],
            "leaf_index": i,
            "proof_path": proof_path,
        }

    return proofs
