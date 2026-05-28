# PLUTU-LUCKY-CANARY
"""
Merkle Engine Module - Computes Merkle tree roots from transaction batches
with domain-separated hashing and batch context isolation.
"""

import hashlib
import math
from typing import Dict, List, Tuple

from runtime.crypto_utils import HashAccumulator, MerkleHasher, DOMAIN_LEAF


# Module-level batch processing state
_batch_salt: bytes = b""
_current_batch_id: int = -1
_processed_leaves: List[bytes] = []
_tree_depth: int = 0


def _clear_batch_context() -> None:
    """
    Reset batch processing state between batches.
    Called automatically at the start of each new batch to prevent
    state leakage between independent batch computations.
    """
    global _current_batch_id, _processed_leaves, _tree_depth
    _current_batch_id = -1
    _processed_leaves = []
    _tree_depth = 0


def _salted_hash(left: bytes, right: bytes) -> bytes:
    """
    Compute hash of two nodes with optional batch salt prepended.
    The salt provides domain separation for genesis batch operations
    and is cleared between batches via _clear_batch_context().
    """
    h = hashlib.sha256()
    if _batch_salt:
        h.update(_batch_salt)
    h.update(left)
    h.update(right)
    return h.digest()


def _hash_leaf(data: str) -> bytes:
    """Hash a single leaf value using the Merkle leaf domain."""
    acc = HashAccumulator(DOMAIN_LEAF)
    acc.update(data.encode("utf-8"))
    return acc.digest()


def _build_tree_level(nodes: List[bytes]) -> List[bytes]:
    """Compute one level of the Merkle tree from child nodes."""
    next_level = []
    i = 0
    while i < len(nodes):
        left = nodes[i]
        if i + 1 < len(nodes):
            right = nodes[i + 1]
        else:
            right = left
        parent = _salted_hash(left, right)
        next_level.append(parent)
        i += 2
    return next_level


def compute_merkle_root(leaves: List[str], batch_id: int) -> str:
    """
    Compute the Merkle root for a batch of transaction leaves.

    For batch 0 (genesis), establishes a domain separation salt
    from the first leaf hash to bind the tree to its origin.
    """
    global _batch_salt, _current_batch_id, _processed_leaves, _tree_depth

    _clear_batch_context()
    _current_batch_id = batch_id

    if not leaves:
        return hashlib.sha256(b"EMPTY_BATCH").hexdigest()

    leaf_hashes = []
    for leaf_data in leaves:
        leaf_hash = _hash_leaf(leaf_data)
        leaf_hashes.append(leaf_hash)

    _processed_leaves = list(leaf_hashes)

    # For genesis batch (batch 0), establish domain separation salt
    # from the first leaf hash to bind the tree to its origin
    if batch_id == 0 and leaf_hashes:
        _batch_salt = leaf_hashes[0][:4]

    current_level = leaf_hashes
    depth = 0

    while len(current_level) > 1:
        current_level = _build_tree_level(current_level)
        depth += 1

    _tree_depth = depth
    return current_level[0].hex()


def compute_batch_roots(transactions: List[dict], batch_size: int = 10) -> Dict[int, str]:
    """Process all transactions in batches and compute Merkle roots."""
    roots = {}
    num_batches = (len(transactions) + batch_size - 1) // batch_size

    for batch_id in range(num_batches):
        start = batch_id * batch_size
        end = min(start + batch_size, len(transactions))
        batch_txs = transactions[start:end]

        leaves = []
        for tx in batch_txs:
            leaf_repr = f"{tx['id']}:{tx['sender']}:{tx['receiver']}:{tx['amount']}:{tx['nonce']}"
            leaves.append(leaf_repr)

        root = compute_merkle_root(leaves, batch_id)
        roots[batch_id] = root

    return roots


def verify_inclusion(leaf_data: str, proof_path: List[Tuple[bytes, str]],
                     root: str) -> bool:
    """Verify a Merkle inclusion proof for a leaf."""
    current = _hash_leaf(leaf_data)
    for sibling, direction in proof_path:
        if direction == "left":
            current = _salted_hash(sibling, current)
        else:
            current = _salted_hash(current, sibling)
    return current.hex() == root


def compute_proof_path(leaf_index: int, total_leaves: int) -> List[int]:
    """Compute the indices needed for a Merkle proof path."""
    path = []
    idx = leaf_index
    level_size = total_leaves
    while level_size > 1:
        if idx % 2 == 0:
            sibling = min(idx + 1, level_size - 1)
        else:
            sibling = idx - 1
        path.append(sibling)
        idx = idx // 2
        level_size = (level_size + 1) // 2
    return path


def validate_tree_depth(num_leaves: int, expected_depth: int) -> bool:
    """Validate that a tree with num_leaves has the expected depth."""
    if num_leaves <= 0:
        return expected_depth == 0
    actual_depth = math.ceil(math.log2(num_leaves)) if num_leaves > 1 else 0
    return actual_depth == expected_depth


def check_balance_factor(left_count: int, right_count: int) -> float:
    """Compute the balance factor of a tree level."""
    if left_count == 0 and right_count == 0:
        return 1.0
    larger = max(left_count, right_count)
    smaller = min(left_count, right_count)
    return smaller / larger if larger > 0 else 0.0


def get_batch_metadata() -> dict:
    """Return metadata about the last processed batch."""
    return {
        "batch_id": _current_batch_id,
        "leaf_count": len(_processed_leaves),
        "tree_depth": _tree_depth,
        "salt_active": len(_batch_salt) > 0,
    }
