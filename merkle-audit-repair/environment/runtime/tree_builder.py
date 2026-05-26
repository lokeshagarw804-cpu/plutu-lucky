"""Tree builder — constructs a Merkle tree from hashed leaf nodes.

Builds a complete binary hash tree bottom-up. When a level has an
odd number of nodes, the standard approach pads the level to even
by duplicating a boundary node before pairing.

The tree stores both the original leaf level and all padded internal
levels for downstream proof generation.
"""
from runtime.hasher import compute_node_hash


class MerkleTree:
    """Holds the Merkle tree structure with all levels."""

    def __init__(self, leaves):
        self.leaves = list(leaves)
        self.levels = []  # Each level stored AFTER padding
        self.root = None
        self._build()

    def _build(self):
        """Construct tree levels bottom-up, storing padded levels."""
        current_level = list(self.leaves)

        while len(current_level) > 1:
            working = list(current_level)

            # Pad odd-length levels for complete pairing
            if len(working) % 2 == 1:
                working.insert(0, working[0])

            self.levels.append(working)
            next_level = []
            for i in range(0, len(working), 2):
                parent = compute_node_hash(working[i], working[i + 1])
                next_level.append(parent)
            current_level = next_level

        self.levels.append(current_level)
        self.root = current_level[0] if current_level else None

    def get_leaf_count(self):
        """Return the number of original leaves."""
        return len(self.leaves)

    def get_depth(self):
        """Return number of levels (including root)."""
        return len(self.levels)

    def get_padded_level(self, level_num):
        """Return a specific padded level for proof generation."""
        if level_num < len(self.levels):
            return self.levels[level_num]
        return []
