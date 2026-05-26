"""Main entry point for the Merkle audit verification system.

Orchestrates the full audit workflow:
1. Parse transaction logs from ledger files
2. Compute leaf hashes for each transaction
3. Build the Merkle tree
4. Generate inclusion proofs for all leaves
5. Verify each proof against the computed root
6. Write audit results to output directory
"""
import json
import os
import sys

sys.path.insert(0, "/app")

from runtime.log_parser import load_transactions
from runtime.hasher import compute_leaf_hash
from runtime.tree_builder import build_merkle_tree
from runtime.proof_engine import generate_all_proofs
from runtime.auditor import run_audit


OUTPUT_DIR = "/app/runtime/output"


def main():
    """Execute the complete Merkle audit verification."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Stage 1: Load transactions from ledger files
    transactions = load_transactions()
    print(f"Loaded {len(transactions)} transactions from ledger files")

    # Stage 2: Compute leaf hashes
    leaf_hashes = [compute_leaf_hash(tx) for tx in transactions]
    print(f"Computed {len(leaf_hashes)} leaf hashes")

    # Stage 3: Build Merkle tree
    tree = build_merkle_tree(leaf_hashes)
    print(f"Built tree with root: {tree['root_hash']}")
    print(f"Tree depth: {tree['depth']}, leaf count: {tree['leaf_count']}")

    # Stage 4: Generate inclusion proofs
    proofs = generate_all_proofs(transactions, leaf_hashes, tree["levels"])
    print(f"Generated {len(proofs)} inclusion proofs")

    # Stage 5: Verify all proofs
    verification = run_audit(transactions, proofs, tree["root_hash"])
    print(
        f"Verification complete: {verification['valid_count']}/{verification['total_proofs']} valid"
    )

    # Stage 6: Write output
    output = {
        "tree": {
            "root_hash": tree["root_hash"],
            "leaf_count": tree["leaf_count"],
            "depth": tree["depth"],
            "level_sizes": [len(level) for level in tree["levels"]],
        },
        "proofs": proofs,
        "verification": verification,
    }

    output_path = os.path.join(OUTPUT_DIR, "audit_result.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Audit results written to {output_path}")
    return output


if __name__ == "__main__":
    main()
