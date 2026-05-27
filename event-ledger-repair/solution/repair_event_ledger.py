#!/usr/bin/env python3
"""Repair script for event ledger replay engine."""
import os
import sys


def patch_loader():
    """Fix account type filtering to strip whitespace from config values."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug A: strip whitespace from comma-separated active_types
    content = content.replace(
        "self._active_types = set(raw_types.split(\",\"))",
        "self._active_types = set(item.strip() for item in raw_types.split(\",\"))"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_sorter():
    """Fix event ordering to include stream_id for deterministic replay."""
    path = "/app/runtime/sorter.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug D: add stream_id to sort key for deterministic ordering
    content = content.replace(
        'all_events.sort(key=lambda e: (e["timestamp"], e["seq"]))',
        'all_events.sort(key=lambda e: (e["timestamp"], e["stream_id"], e["seq"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_aggregator():
    """Fix window balance update to use assignment instead of accumulation."""
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug C: replace += accumulation with = assignment
    old_block = """                    if stream not in windows[win_idx]["balances"]:
                        windows[win_idx]["balances"][stream] = 0.0
                    windows[win_idx]["balances"][stream] += snapshot["balance"]"""

    new_block = """                    windows[win_idx]["balances"][stream] = snapshot["balance"]"""

    content = content.replace(old_block, new_block)

    with open(path, "w") as f:
        f.write(content)


def patch_reconciler():
    """Fix config section to read from reconciliation.strict."""
    path = "/app/runtime/reconciler.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug B: read from reconciliation.strict section
    content = content.replace(
        'self._threshold = self._config.getfloat(\n            "reconciliation", "balance_threshold"\n        )',
        'self._threshold = self._config.getfloat(\n            "reconciliation.strict", "balance_threshold"\n        )'
    )
    content = content.replace(
        'self._min_consecutive = self._config.getint(\n            "reconciliation", "min_consecutive_windows"\n        )',
        'self._min_consecutive = self._config.getint(\n            "reconciliation.strict", "min_consecutive_windows"\n        )'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_sorter()
    patch_aggregator()
    patch_reconciler()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_ledger import main as run_main
    run_main()


if __name__ == "__main__":
    main()
