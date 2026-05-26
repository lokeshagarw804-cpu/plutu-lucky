#!/usr/bin/env python3
"""Repair script for audit chain verifier. Patches all defects and re-runs."""
import os
import sys


def patch_loader():
    """Fix Bug A: strip whitespace from comma-split stream list."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._active_streams = set(raw_streams.split(","))',
        'self._active_streams = set(s.strip() for s in raw_streams.split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_hasher():
    """Fix Bug B: read key_length from verification.hmac section."""
    path = "/app/runtime/hasher.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._key_length = self._config.getint("hmac", "key_length")',
        'self._key_length = self._config.getint("verification.hmac", "key_length")'
    )
    content = content.replace(
        'self._digest_bytes = self._config.getint("hmac", "digest_bytes")',
        'self._digest_bytes = self._config.getint("verification.hmac", "digest_bytes")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_integrity_scorer():
    """Fix Bug C: compute per-stream scores independently."""
    path = "/app/runtime/integrity_scorer.py"
    with open(path, "r") as f:
        content = f.read()

    old_code = '''        # Compute per-stream scores from running totals
        per_stream = {}
        for sid, stats in stream_stats.items():
            if stats["total"] > 0:
                per_stream[sid] = round(
                    running_valid / running_total, 4
                )
            else:
                per_stream[sid] = 1.0'''

    new_code = '''        # Compute per-stream scores independently
        per_stream = {}
        for sid, stats in stream_stats.items():
            if stats["total"] > 0:
                per_stream[sid] = round(
                    stats["valid"] / stats["total"], 4
                )
            else:
                per_stream[sid] = 1.0'''

    content = content.replace(old_code, new_code)

    with open(path, "w") as f:
        f.write(content)


def patch_tamper_detector():
    """Fix Bug D: add stream_id as tiebreaker in tampered entry sort."""
    path = "/app/runtime/tamper_detector.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'tampered.sort(key=lambda t: (t["timestamp"], t["seq"]))',
        'tampered.sort(key=lambda t: (t["timestamp"], t["stream_id"], t["seq"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_verifier():
    """Fix Bug E: remove off-by-one in verification window step."""
    path = "/app/runtime/verifier.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "        for i in range(0, len(chain_results), self._window_size + 1):\n"
        "            window_entries = chain_results[i:i + self._window_size + 1]",
        "        for i in range(0, len(chain_results), self._window_size):\n"
        "            window_entries = chain_results[i:i + self._window_size]"
    )

    content = content.replace(
        "        return math.ceil(entry_count / (self._window_size + 1))",
        "        return math.ceil(entry_count / self._window_size)"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_hasher()
    patch_integrity_scorer()
    patch_tamper_detector()
    patch_verifier()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_audit import main as run_main
    run_main()


if __name__ == "__main__":
    main()
