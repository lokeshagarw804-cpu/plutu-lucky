#!/usr/bin/env python3
"""Repair script for event ledger replay engine."""
import os
import sys


def patch_loader():
    """Fix account type filtering to handle whitespace in config values."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "self._active_types = set(raw_types.split(\",\"))",
        "self._active_types = set(item.strip() for item in raw_types.split(\",\"))"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_aggregator():
    """Fix window balance finalization to use last snapshot value."""
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()

    # The bug: computes average of all intermediate running-balance snapshots
    # for a stream within a window. Since each snapshot is the cumulative
    # running total after processing that event, the correct final balance
    # is simply the LAST snapshot value (the state after the final event).
    content = content.replace(
        "window[\"balances\"][stream_id] = sum(balance_history) / len(balance_history)",
        "window[\"balances\"][stream_id] = balance_history[-1]"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_reconciler():
    """Fix reconciler to use production sensitivity parameters."""
    path = "/app/runtime/reconciler.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._threshold = self._config.getfloat(\n            "reconciliation", "balance_threshold"\n        )',
        'self._threshold = self._config.getfloat(\n            "reconciliation.strict", "balance_threshold"\n        )'
    )
    content = content.replace(
        'self._min_consecutive = self._config.getint(\n            "reconciliation", "min_consecutive_windows"\n        )',
        'self._min_consecutive = self._config.getint(\n            "reconciliation.strict", "min_consecutive_windows"\n        )'
    )
    content = content.replace(
        'self._severity_cutoff = self._config.getint(\n            "reconciliation", "severity_cutoff"\n        )',
        'self._severity_cutoff = self._config.getint(\n            "reconciliation.strict", "severity_cutoff"\n        )'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
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
