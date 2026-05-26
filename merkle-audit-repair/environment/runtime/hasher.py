"""Hasher — computes cryptographic hashes for Merkle tree nodes.

Provides leaf hashing (from transaction fields) and internal node
hashing (from child pair concatenation). Uses SHA-256 throughout.
"""
import hashlib


FIELD_SEPARATOR = "|"


def compute_leaf_hash(transaction):
    """Compute SHA-256 hash of a transaction's canonical representation.

    Canonical field order for hashing: amount, account, txn_type, timestamp.
    Fields are joined by the module-level FIELD_SEPARATOR.
    """
    canonical = FIELD_SEPARATOR.join([
        transaction["amount"],
        transaction["account"],
        transaction["txn_type"],
        transaction["timestamp"],
    ])
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_node_hash(left_hash, right_hash):
    """Compute SHA-256 hash of two child hashes concatenated.

    Convention: left child hash is prepended to right child hash,
    separated by FIELD_SEPARATOR, then hashed.
    """
    combined = left_hash + FIELD_SEPARATOR + right_hash
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()
