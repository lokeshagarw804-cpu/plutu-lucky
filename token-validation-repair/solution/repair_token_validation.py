"""Repair script for the HMAC Token Batch Validator.

Fixes four bugs in the validation system:
A) policy_checker.py reads from wrong config section for clock drift
B) signature_verifier.py uses base64-encoded key as raw string instead of decoding
C) token_loader.py sorts batch files lexicographically instead of numerically
D) trust_scorer.py applies incorrect decay exponent (distance+1 instead of distance)
"""

import re


def fix_policy_checker():
    """Fix Bug A: Read max_clock_drift_sec from [policy.strict] section."""
    path = "/app/runtime/policy_checker.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'max_drift = int(config.get("policy", "max_clock_drift_sec"))',
        'max_drift = int(config.get("policy.strict", "max_clock_drift_sec"))'
    )

    with open(path, "w") as f:
        f.write(content)


def fix_signature_verifier():
    """Fix Bug B: Decode base64 signing key before using in HMAC."""
    path = "/app/runtime/signature_verifier.py"
    with open(path, "r") as f:
        content = f.read()

    # Add base64 import
    content = content.replace(
        "import hmac\nimport hashlib\nimport configparser",
        "import hmac\nimport hashlib\nimport base64\nimport configparser"
    )

    # Fix key decoding
    content = content.replace(
        'return key_str.encode("utf-8")',
        "return base64.b64decode(key_str)"
    )

    with open(path, "w") as f:
        f.write(content)


def fix_token_loader():
    """Fix Bug C: Sort batch files numerically by extracting number from filename."""
    path = "/app/runtime/token_loader.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "batch_files = sorted(batch_files)",
        'batch_files = sorted(batch_files, key=lambda f: int(f.split("_")[1].split(".")[0]))'
    )

    with open(path, "w") as f:
        f.write(content)


def fix_trust_scorer():
    """Fix Bug D: Use distance instead of distance+1 in decay formula."""
    path = "/app/runtime/trust_scorer.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "score = base_score * (decay_factor ** (distance + 1))",
        "score = base_score * (decay_factor ** distance)"
    )

    with open(path, "w") as f:
        f.write(content)


if __name__ == "__main__":
    fix_policy_checker()
    fix_signature_verifier()
    fix_token_loader()
    fix_trust_scorer()
    print("All repairs applied successfully.")
