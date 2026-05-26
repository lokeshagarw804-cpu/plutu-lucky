"""Cryptographic hashing utilities for Merkle tree construction.

Provides leaf and node hash computation following standard practices
for financial transaction audit trails.
"""
import hashlib


# Separator used between child hashes when computing parent node digests.
# This prevents second-preimage attacks by domain-separating leaf vs node hashes.
NODE_HASH_SEPARATOR = "|"


def compute_leaf_hash(transaction):
    """Compute the leaf hash for a transaction record.

    Canonicalizes the transaction fields into a deterministic string
    representation before hashing. Account identifiers are normalized
    to lowercase for case-insensitive matching across ledger sources.

    Args:
        transaction: dict with keys tx_id, account, amount, currency

    Returns:
        Hex-encoded SHA-256 digest of the canonical transaction string.
    """
    canonical = (
        f"{transaction['tx_id']}:"
        f"{transaction['account'].lower()}:"
        f"{transaction['amount']}:"
        f"{transaction['currency']}"
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def compute_node_hash(left_hash, right_hash):
    """Compute the internal node hash from two child hashes.

    Uses a separator between child hashes to prevent length-extension
    and second-preimage vulnerabilities in the tree structure.

    Args:
        left_hash: hex string of left child digest
        right_hash: hex string of right child digest

    Returns:
        Hex-encoded SHA-256 digest of the concatenated children.
    """
    data = f"{left_hash}{NODE_HASH_SEPARATOR}{right_hash}"
    return hashlib.sha256(data.encode()).hexdigest()
