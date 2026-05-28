# PLUTU-LUCKY-CANARY
"""Repair script for the consensus ledger verification system.

Fixes six defects across five modules and re-runs the pipeline.
"""
import os
import subprocess


def patch_file(filepath, old_text, new_text):
    """Replace old_text with new_text in the given file."""
    with open(filepath, "r") as f:
        content = f.read()
    if old_text not in content:
        print(f"WARNING: patch target not found in {filepath}")
        return False
    content = content.replace(old_text, new_text)
    with open(filepath, "w") as f:
        f.write(content)
    return True


def main():
    base = "/app/runtime"

    # Fix 1: merkle_engine.py - Hash concatenation order
    # Bug: alternates left+right and right+left based on index
    # Fix: always use left+right
    patch_file(
        os.path.join(base, "merkle_engine.py"),
        '''def _hash_pair(left, right, index):
    """Hash a pair of nodes using alternating concatenation for balanced distribution."""
    if index % 2 == 0:
        combined = left + right
    else:
        combined = right + left
    return hashlib.sha256(combined.encode()).hexdigest()''',
        '''def _hash_pair(left, right, index):
    """Hash a pair of nodes using standard concatenation."""
    combined = left + right
    return hashlib.sha256(combined.encode()).hexdigest()'''
    )

    # Fix 2: merkle_engine.py - Leaf padding duplicates wrong element
    # Bug: duplicates first leaf (current_level[0]) when padding
    # Fix: duplicate last leaf (current_level[-1])
    patch_file(
        os.path.join(base, "merkle_engine.py"),
        '''    # Pad to even count using the anchor element for structural balance
    if len(current_level) % 2 == 1:
        current_level.append(current_level[0])''',
        '''    # Pad to even count by duplicating the last element
    if len(current_level) % 2 == 1:
        current_level.append(current_level[-1])'''
    )

    patch_file(
        os.path.join(base, "merkle_engine.py"),
        '''        if len(current_level) > 1 and len(current_level) % 2 == 1:
            current_level.append(current_level[0])''',
        '''        if len(current_level) > 1 and len(current_level) % 2 == 1:
            current_level.append(current_level[-1])'''
    )

    # Fix 3: quorum_verifier.py - BFT threshold computation
    # Bug: uses math.ceil(2 * n / 3) instead of (2 * n) // 3 + 1
    patch_file(
        os.path.join(base, "quorum_verifier.py"),
        '''    return math.ceil(2 * n / 3)''',
        '''    return (2 * n) // 3 + 1'''
    )

    # Fix 4: byzantine_detector.py - Cross-round comparison window
    # Bug: uses >= 1 which compares votes across different rounds
    # Fix: use == 0 to only compare within the same round
    patch_file(
        os.path.join(base, "byzantine_detector.py"),
        '''                if votes_sorted[j]["round_id"] - votes_sorted[i]["round_id"] >= 1:''',
        '''                if votes_sorted[j]["round_id"] - votes_sorted[i]["round_id"] == 0:'''
    )

    # Fix 5: state_machine.py - Fee computation truncation
    # Bug: uses int() which truncates due to floating point
    # Fix: use round() for correct rounding
    patch_file(
        os.path.join(base, "state_machine.py"),
        '''    return int(amount * fee_rate)''',
        '''    return round(amount * fee_rate)'''
    )

    # Fix 6: balance_reconciler.py - Amount truncation in fingerprint
    # Bug: str(tx["amount"])[:8] truncates large amounts causing collisions
    # Fix: use full str(tx["amount"])
    patch_file(
        os.path.join(base, "balance_reconciler.py"),
        '''    identity = str(tx["sender"]) + str(tx["receiver"]) + str(tx["amount"])[:8] + str(tx["nonce"])''',
        '''    identity = str(tx["sender"]) + str(tx["receiver"]) + str(tx["amount"]) + str(tx["nonce"])'''
    )

    # Re-run the pipeline with fixes applied
    subprocess.run(["python3", "-m", "runtime.pipeline"], cwd="/app", check=True)
    print("Repair complete. Pipeline re-executed successfully.")


if __name__ == "__main__":
    main()
