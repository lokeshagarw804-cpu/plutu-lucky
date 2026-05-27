#!/usr/bin/env python3
"""Repair script for event replay engine. Patches bugs and re-runs."""
import os
import sys


def patch_loader():
    """Fix Bug A: strip whitespace from comma-separated stream names."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._active = set(raw_streams.split(","))',
        'self._active = set(s.strip() for s in raw_streams.split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_sequencer():
    """Fix Bug B: read batch_size from replay.incremental section.
    Fix Bug D: add stream_id to sort key for deterministic ordering.
    """
    path = "/app/runtime/sequencer.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug B: wrong config section for batch_size
    content = content.replace(
        'self._batch_size = self._config.getint("replay", "batch_size")',
        'self._batch_size = self._config.getint("replay.incremental", "batch_size")'
    )

    # Fix Bug D: add stream_id to sort key
    content = content.replace(
        'all_events.sort(key=lambda e: (e["timestamp"], e["sequence"]))',
        'all_events.sort(key=lambda e: (e["timestamp"], e["stream_id"], e["sequence"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_aggregator():
    """Fix Bug C: gauge fields should use last-write-wins (=) not accumulate (+=)."""
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()

    # Replace the buggy gauge field logic
    old_gauge = '''                if key in GAUGE_FIELDS:
                    # Gauge: accumulate values for running total per snapshot
                    if key in state["fields"] and isinstance(value, (int, float)):
                        state["fields"][key] += value
                    else:
                        state["fields"][key] = value'''

    new_gauge = '''                if key in GAUGE_FIELDS:
                    # Gauge: last-write-wins for current state
                    state["fields"][key] = value'''

    content = content.replace(old_gauge, new_gauge)

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_sequencer()
    patch_aggregator()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_replay import main as run_main
    run_main()


if __name__ == "__main__":
    main()
