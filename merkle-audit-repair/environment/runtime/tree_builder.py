"""Merkle tree construction from transaction leaf hashes.

Builds a complete binary Merkle tree using the standard approach of
padding odd-length levels by duplicating the final node. Employs
double-SHA256 for internal nodes following the hardened hash convention
used in cryptocurrency transaction verification systems.
"""
import hashlib

from runtime.hasher import NODE_HASH_SEPARATOR


def _hardened_node_hash(left_hash, right_hash):
    """Compute hardened double-SHA256 node hash.

    Applies SHA-256 twice to the concatenated child hashes, following
    the Bitcoin Merkle tree convention for protection against
    length-extension attacks on the internal hash state.

    Args:
        left_hash: hex string of left child digest
        right_hash: hex string of right child digest

    Returns:
        Hex-encoded double-SHA256 digest.
    """
    inner_data = f"{left_hash}{NODE_HASH_SEPARATOR}{right_hash}"
    inner_hash = hashlib.sha256(inner_data.encode()).hexdigest()
    return hashlib.sha256(inner_hash.encode()).hexdigest()


def build_merkle_tree(leaf_hashes):
    """Construct a Merkle tree from a list of leaf hashes.

    Builds the tree bottom-up. At each level, if the node count is odd,
    the last node is duplicated to create a balanced binary tree. The
    tree uses hardened double-SHA256 for internal node computation.

    Args:
        leaf_hashes: list of hex-encoded leaf digests

    Returns:
        dict with keys:
            - root_hash: the hex root digest
            - levels: list of lists, from leaves (level 0) to root
            - depth: number of levels in the tree
            - leaf_count: number of original leaves
    """
    if not leaf_hashes:
        return {"root_hash": None, "levels": [], "depth": 0, "leaf_count": 0}

    levels = [leaf_hashes[:]]
    current = leaf_hashes[:]

    while len(current) > 1:
        # Pad odd-length levels by duplicating the last element
        if len(current) % 2 == 1:
            current.append(current[-1])

        next_level = []
        for i in range(0, len(current), 2):
            parent = _hardened_node_hash(current[i], current[i + 1])
            next_level.append(parent)

        current = next_level
        levels.append(current[:])

    return {
        "root_hash": levels[-1][0],
        "levels": levels,
        "depth": len(levels),
        "leaf_count": len(leaf_hashes),
    }
