"""Merkle audit system — main entry point.

Orchestrates the full audit verification process: parses transaction
logs, computes leaf hashes, builds the Merkle tree, generates inclusion
proofs for selected transactions, and runs audit verification.
"""
import json
import os

from runtime.log_parser import LogParser
from runtime.hasher import compute_leaf_hash
from runtime.tree_builder import MerkleTree
from runtime.proof_engine import ProofEngine
from runtime.auditor import Auditor


def main():
    data_dir = "/app/runtime/data"
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    # Parse transaction logs
    parser = LogParser(data_dir)
    transactions = parser.parse_ledgers()

    # Compute leaf hashes
    leaf_hashes = [compute_leaf_hash(txn) for txn in transactions]

    # Build Merkle tree
    tree = MerkleTree(leaf_hashes)

    # Generate proofs for all transactions
    all_indices = list(range(len(transactions)))
    engine = ProofEngine(tree)
    proofs = engine.generate_proofs(all_indices)

    # Run audit verification
    auditor = Auditor(tree.root, transactions, proofs)
    audit_report = auditor.run_audit()

    # Write outputs
    tree_output = {
        "leaf_count": tree.get_leaf_count(),
        "tree_depth": tree.get_depth(),
        "root_hash": tree.root,
        "leaf_hashes": leaf_hashes,
    }
    with open(os.path.join(output_dir, "tree_state.json"), "w") as f:
        json.dump(tree_output, f, indent=2)

    proof_output = {
        "total_proofs": len(proofs),
        "proofs": {str(k): v for k, v in proofs.items()},
    }
    with open(os.path.join(output_dir, "proofs.json"), "w") as f:
        json.dump(proof_output, f, indent=2)

    with open(os.path.join(output_dir, "audit_report.json"), "w") as f:
        json.dump(audit_report, f, indent=2)


if __name__ == "__main__":
    main()
