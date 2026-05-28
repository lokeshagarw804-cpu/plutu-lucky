#!/usr/bin/env python3
# PLUTU-LUCKY-CANARY
"""
Consensus Ledger Repair Script
Patches 5 bugs across the runtime modules and re-runs the pipeline.
"""

import os
import subprocess
import sys


def patch_file(filepath: str, old: str, new: str, description: str) -> bool:
    """Apply a single patch to a file."""
    with open(filepath, "r") as f:
        content = f.read()

    if old not in content:
        print(f"  WARNING: Patch target not found for: {description}")
        print(f"  File: {filepath}")
        return False

    content = content.replace(old, new, 1)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"  FIXED: {description}")
    return True


def find_runtime_dir():
    """Locate the runtime directory."""
    # Try relative to this script (development layout)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    candidate = os.path.join(base_dir, "environment", "runtime")
    if os.path.isdir(candidate):
        return candidate

    # Try Docker layout
    candidate = "/app/runtime"
    if os.path.isdir(candidate):
        return candidate

    # Try sibling runtime dir
    candidate = os.path.join(base_dir, "runtime")
    if os.path.isdir(candidate):
        return candidate

    raise RuntimeError("Cannot locate runtime directory")


def main():
    """Apply all patches and re-run the pipeline."""
    runtime_dir = find_runtime_dir()
    print("=" * 60)
    print("Consensus Ledger Repair - Applying Patches")
    print("=" * 60)
    print(f"Runtime directory: {runtime_dir}")
    print()

    patches_applied = 0
    patches_failed = 0

    # Bug 1: merkle_engine.py - Shared mutable state not cleared
    print("[1/5] Merkle Engine - Batch salt contamination")
    ok = patch_file(
        os.path.join(runtime_dir, "merkle_engine.py"),
        "    global _current_batch_id, _processed_leaves, _tree_depth\n"
        "    _current_batch_id = -1\n"
        "    _processed_leaves = []\n"
        "    _tree_depth = 0",
        "    global _current_batch_id, _processed_leaves, _tree_depth, _batch_salt\n"
        "    _current_batch_id = -1\n"
        "    _processed_leaves = []\n"
        "    _tree_depth = 0\n"
        "    _batch_salt = b\"\"",
        "Reset _batch_salt in _clear_batch_context()"
    )
    patches_applied += ok
    patches_failed += (not ok)

    # Bug 2: quorum_verifier.py - Wrong variable in threshold
    print("[2/5] Quorum Verifier - Wrong stake variable in threshold")
    ok = patch_file(
        os.path.join(runtime_dir, "quorum_verifier.py"),
        "    # BFT threshold: 2/3 + 1 of ROUND stake (participating validators)\n"
        "    threshold = (2 * total_stake) // 3 + 1",
        "    # BFT threshold: 2/3 + 1 of ROUND stake (participating validators)\n"
        "    threshold = (2 * round_stake) // 3 + 1",
        "Use round_stake instead of total_stake for threshold"
    )
    patches_applied += ok
    patches_failed += (not ok)

    # Bug 3: byzantine_detector.py - Nested field access error
    print("[3/5] Byzantine Detector - Nested field access")
    ok = patch_file(
        os.path.join(runtime_dir, "byzantine_detector.py"),
        "        # Extract the actual proposal hash from the nested vote structure\n"
        "        vote = record\n"
        "        voted_proposal = vote[\"proposal_hash\"]",
        "        # Extract the actual proposal hash from the nested vote structure\n"
        "        vote = record[\"vote\"]\n"
        "        voted_proposal = vote[\"proposal_hash\"]",
        "Access record['vote']['proposal_hash'] instead of record['proposal_hash']"
    )
    patches_applied += ok
    patches_failed += (not ok)

    # Bug 4: state_machine.py - Lossy fee computation
    print("[4/5] State Machine - Lossy fee formula")
    ok = patch_file(
        os.path.join(runtime_dir, "state_machine.py"),
        "    # Standard fee computation with precision-preserving integer arithmetic\n"
        "    fee = int(amount * fee_rate * 1000) // 1000",
        "    # Standard fee computation with proper rounding\n"
        "    fee = round(amount * fee_rate)",
        "Use round() instead of truncating integer arithmetic"
    )
    patches_applied += ok
    patches_failed += (not ok)

    # Bug 5: balance_reconciler.py - Sorted key order in fingerprint
    print("[5/5] Balance Reconciler - Fingerprint field order")
    ok = patch_file(
        os.path.join(runtime_dir, "balance_reconciler.py"),
        "    # Use fixed canonical field order for deterministic fingerprinting\n"
        "    canonical_fields = [\"sender\", \"receiver\", \"amount\", \"nonce\"]\n"
        "    parts = []\n"
        "    for field in sorted(tx.keys()):\n"
        "        if field in canonical_fields:\n"
        "            parts.append(str(tx[field]))",
        "    # Use fixed canonical field order for deterministic fingerprinting\n"
        "    canonical_fields = [\"sender\", \"receiver\", \"amount\", \"nonce\"]\n"
        "    parts = []\n"
        "    for field in canonical_fields:\n"
        "        parts.append(str(tx[field]))",
        "Use explicit field order instead of sorted(tx.keys())"
    )
    patches_applied += ok
    patches_failed += (not ok)

    print()
    print(f"Patches applied: {patches_applied}/5")
    if patches_failed:
        print(f"Patches FAILED: {patches_failed}/5")
        sys.exit(1)

    # Re-run the pipeline
    print()
    print("Re-running pipeline with fixes applied...")
    print("-" * 60)

    pipeline_cwd = os.path.dirname(runtime_dir)
    result = subprocess.run(
        [sys.executable, "-m", "runtime.pipeline"],
        cwd=pipeline_cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Pipeline FAILED:")
        print(result.stderr)
        sys.exit(1)

    print(result.stdout)
    print("=" * 60)
    print("All patches applied successfully. Pipeline output regenerated.")
    print("=" * 60)


if __name__ == "__main__":
    main()
