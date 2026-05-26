#!/usr/bin/env python3
"""Repair script for Merkle audit verification system."""
import os
import sys


def patch_hasher():
    """Fix Bug E: remove .lower() from leaf hash computation.

    The hasher normalizes account IDs to lowercase during tree building,
    but the auditor's reconstruct_leaf_hash does not. Remove .lower()
    so both use the original case.
    """
    path = "/app/runtime/hasher.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "{transaction['account'].lower()}:",
        "{transaction['account']}:"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_tree_builder():
    """Fix Bug A: replace double-SHA256 with single SHA256.

    The tree builder uses sha256(sha256(data)) but the auditor and
    hasher.compute_node_hash use single sha256. Remove the outer wrap.
    """
    path = "/app/runtime/tree_builder.py"
    with open(path, "r") as f:
        content = f.read()

    # Replace the _hardened_node_hash function body to use single SHA256
    old_fn = '''def _hardened_node_hash(left_hash, right_hash):
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
    return hashlib.sha256(inner_hash.encode()).hexdigest()'''

    new_fn = '''def _hardened_node_hash(left_hash, right_hash):
    """Compute node hash from child hashes.

    Args:
        left_hash: hex string of left child digest
        right_hash: hex string of right child digest

    Returns:
        Hex-encoded SHA-256 digest.
    """
    data = f"{left_hash}{NODE_HASH_SEPARATOR}{right_hash}"
    return hashlib.sha256(data.encode()).hexdigest()'''

    content = content.replace(old_fn, new_fn)

    with open(path, "w") as f:
        f.write(content)


def patch_proof_engine():
    """Fix Bug B: use idx // 2 instead of (idx + 1) // 2 for parent index.

    The (idx + 1) // 2 formula is for 1-based indexing but the code
    uses 0-based indices. This causes wrong sibling selection for
    odd-indexed leaves.
    """
    path = "/app/runtime/proof_engine.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "idx = (idx + 1) // 2",
        "idx = idx // 2"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_log_parser():
    """Fix Bug C: sort ledger files by numeric suffix instead of string.

    String sort produces ledger_1, ledger_10, ledger_2 order.
    Numeric sort produces ledger_1, ledger_2, ledger_10 order.
    """
    path = "/app/runtime/log_parser.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'ledger_files = sorted(\n        f for f in os.listdir(DATA_DIR) if f.startswith("ledger_") and f.endswith(".json")\n    )',
        'ledger_files = sorted(\n        (f for f in os.listdir(DATA_DIR) if f.startswith("ledger_") and f.endswith(".json")),\n        key=lambda f: int(f.split("_")[1].split(".")[0])\n    )'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_auditor():
    """Fix Bug D: add separator in auditor's _compute_parent_hash.

    The tree builder uses NODE_HASH_SEPARATOR ("|") between children,
    but the auditor concatenates without separator. Add the separator.
    """
    path = "/app/runtime/auditor.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'data = f"{left_hash}{right_hash}"',
        'data = f"{left_hash}|{right_hash}"'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_hasher()
    patch_tree_builder()
    patch_proof_engine()
    patch_log_parser()
    patch_auditor()

    # Re-import and run
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_audit import main as run_main
    run_main()


if __name__ == "__main__":
    main()
