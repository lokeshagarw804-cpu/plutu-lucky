#!/usr/bin/env python3
"""Repair script for the certificate chain verification system.

Patches the four defects and re-runs the system to produce correct output.
"""
import os
import sys


def patch_validator():
    """Fix Bug A: trusted_roots parsing does not strip whitespace."""
    path = "/app/runtime/validator.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._trusted_roots = set(raw_roots.split(","))',
        'self._trusted_roots = set(item.strip() for item in raw_roots.split(","))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_chain_builder_section():
    """Fix Bug B: chain_builder reads from wrong config section."""
    path = "/app/runtime/chain_builder.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._max_depth = config.getint("validation", "max_chain_depth")',
        'self._max_depth = config.getint("validation.strict", "max_chain_depth")'
    )
    content = content.replace(
        'self._decay_factor = config.getfloat("validation", "score_decay_factor")',
        'self._decay_factor = config.getfloat("validation.strict", "score_decay_factor")'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_chain_builder_score():
    """Fix Bug C: trust score uses shared cache that accumulates across chains."""
    path = "/app/runtime/chain_builder.py"
    with open(path, "r") as f:
        content = f.read()
    old_code = '''        score = 0.0
        for i, cert_id in enumerate(chain_ids):
            hop_contribution = 0.0
            if cert_id in valid_map and valid_map[cert_id]["fully_valid"]:
                hop_contribution = (1.0 - self._decay_factor) ** i
            self._score_cache[cert_id] = (
                self._score_cache.get(cert_id, 0.0) + hop_contribution
            )
            score += self._score_cache[cert_id]
        return round(score, 4)'''
    new_code = '''        score = 0.0
        for i, cert_id in enumerate(chain_ids):
            if cert_id in valid_map and valid_map[cert_id]["fully_valid"]:
                score += (1.0 - self._decay_factor) ** i
        return round(score, 4)'''
    content = content.replace(old_code, new_code)
    with open(path, "w") as f:
        f.write(content)


def patch_reporter_sort():
    """Fix Bug D: sort key missing issuer_id for deterministic ordering."""
    path = "/app/runtime/reporter.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'key=lambda e: (e["expiry_date"], e["serial"])',
        'key=lambda e: (e["expiry_date"], e["issuer_id"], e["serial"])'
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_validator()
    patch_chain_builder_section()
    patch_chain_builder_score()
    patch_reporter_sort()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_crypto import main as run_main
    run_main()


if __name__ == "__main__":
    main()
