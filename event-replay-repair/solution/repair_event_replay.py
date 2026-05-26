#!/usr/bin/env python3
"""Repair script for CQRS event replay engine."""
import os
import sys


def patch_stream_loader():
    """Fix Bug A: strip whitespace from comma-separated stream names."""
    path = "/app/runtime/stream_loader.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._included = set(raw_streams.split(","))',
        'self._included = set(s.strip() for s in raw_streams.split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_reconciler():
    """Fix Bug B: read decimal_places from correct config section."""
    path = "/app/runtime/reconciler.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._decimals = self._config.getint("projection", "decimal_places")',
        'self._decimals = self._config.getint("projection.reconciliation", "decimal_places")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_snapshot_builder():
    """Fix Bug C: record point-in-time balances instead of accumulating."""
    path = "/app/runtime/snapshot_builder.py"
    with open(path, "r") as f:
        content = f.read()

    # Replace the accumulation logic with direct balance copy
    old_code = """                for aid, bal in balances.items():
                    cumulative[aid] += bal
                    snapshot["balances"][aid] = cumulative[aid]"""

    new_code = """                for aid, bal in balances.items():
                    snapshot["balances"][aid] = bal"""

    content = content.replace(old_code, new_code)

    with open(path, "w") as f:
        f.write(content)


def patch_sequencer():
    """Fix Bug D: add stream_id to sort key for deterministic ordering."""
    path = "/app/runtime/sequencer.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'all_events.sort(key=lambda e: (e["timestamp"], e["sequence_num"]))',
        'all_events.sort(key=lambda e: (e["timestamp"], e["stream_id"], e["sequence_num"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_stream_loader()
    patch_reconciler()
    patch_snapshot_builder()
    patch_sequencer()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_replay import main as run_main
    run_main()


if __name__ == "__main__":
    main()
