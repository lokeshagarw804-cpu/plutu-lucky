#!/usr/bin/env python3
"""Repair script for Merkle audit verification system."""
import sys


def patch_hasher():
    """Fix Bug A: correct canonical field order for leaf hashing."""
    path = "/app/runtime/hasher.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix field order: was amount|account|txn_type|timestamp
    # Should be: timestamp|account|txn_type|amount
    content = content.replace(
        '''    canonical = FIELD_SEPARATOR.join([
        transaction["amount"],
        transaction["account"],
        transaction["txn_type"],
        transaction["timestamp"],
    ])''',
        '''    canonical = FIELD_SEPARATOR.join([
        transaction["timestamp"],
        transaction["account"],
        transaction["txn_type"],
        transaction["amount"],
    ])'''
    )

    with open(path, "w") as f:
        f.write(content)


def patch_tree_builder():
    """Fix Bug B: duplicate last node for odd padding, not first."""
    path = "/app/runtime/tree_builder.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "working.insert(0, working[0])",
        "working.append(working[-1])"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_proof_engine():
    """Fix Bug C: direction indicates sibling's side, not target's."""
    path = "/app/runtime/proof_engine.py"
    with open(path, "r") as f:
        content = f.read()

    # When target is at even index, sibling is to the RIGHT
    # When target is at odd index, sibling is to the LEFT
    content = content.replace(
        '''            if idx % 2 == 0:
                sibling_idx = idx + 1
                direction = "left"
            else:
                sibling_idx = idx - 1
                direction = "right"''',
        '''            if idx % 2 == 0:
                sibling_idx = idx + 1
                direction = "right"
            else:
                sibling_idx = idx - 1
                direction = "left"'''
    )

    with open(path, "w") as f:
        f.write(content)


def patch_auditor():
    """Fix Bug D: use same separator as hasher module for leaf reconstruction."""
    path = "/app/runtime/auditor.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix separator: was "-", should be FIELD_SEPARATOR ("|")
    content = content.replace(
        '    canonical = "-".join([',
        '    canonical = FIELD_SEPARATOR.join(['
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_hasher()
    patch_tree_builder()
    patch_proof_engine()
    patch_auditor()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_audit import main as run_main
    run_main()


if __name__ == "__main__":
    main()
