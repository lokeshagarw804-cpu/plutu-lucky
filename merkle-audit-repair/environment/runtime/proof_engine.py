"""Proof engine — generates Merkle inclusion proofs.

An inclusion proof for a leaf consists of the sequence of sibling
hashes needed to reconstruct the root hash. Each step includes
the sibling hash and a direction indicator specifying which side
the sibling node is on relative to the path being verified.

The engine reads padded levels directly from the tree structure
to ensure proof generation is consistent with how the tree was built.
"""


class ProofStep:
    """A single step in a Merkle inclusion proof."""

    def __init__(self, sibling_hash, direction):
        self.sibling_hash = sibling_hash
        self.direction = direction

    def to_dict(self):
        return {"sibling_hash": self.sibling_hash, "direction": self.direction}


class ProofEngine:
    """Generates inclusion proofs from a Merkle tree."""

    def __init__(self, tree):
        self._tree = tree

    def generate_proof(self, leaf_index):
        """Generate inclusion proof for leaf at given index.

        Walks the tree's stored padded levels from bottom to root.

        Direction semantics: indicates which side the SIBLING is on.
        """
        if leaf_index < 0 or leaf_index >= self._tree.get_leaf_count():
            return None

        proof_steps = []
        idx = leaf_index

        for level_num in range(self._tree.get_depth() - 1):
            level = self._tree.get_padded_level(level_num)

            # Determine sibling position and direction
            if idx % 2 == 0:
                sibling_idx = idx + 1
                direction = "left"
            else:
                sibling_idx = idx - 1
                direction = "right"

            if sibling_idx < len(level):
                sibling_hash = level[sibling_idx]
            else:
                sibling_hash = level[-1]

            proof_steps.append(ProofStep(sibling_hash, direction))
            idx = idx // 2

        return proof_steps

    def generate_proofs(self, indices):
        """Generate proofs for multiple leaf indices."""
        results = {}
        for i in indices:
            proof = self.generate_proof(i)
            if proof is not None:
                results[i] = [step.to_dict() for step in proof]
        return results
