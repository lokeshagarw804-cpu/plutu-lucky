#!/usr/bin/env python3
"""Repair script for the event replay projection system.

Patches the four defects and re-runs the system to produce correct output.
"""
import os
import sys


def patch_filter():
    """Fix Bug A: event_types parsing does not strip whitespace."""
    path = "/app/runtime/filter.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._allowed_types = set(raw_types.split(","))',
        'self._allowed_types = set(t.strip() for t in raw_types.split(","))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_projector_section():
    """Fix Bug B: projector reads from wrong config section."""
    path = "/app/runtime/projector.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._batch_window_hours = config.getint(\n            "replay", "batch_window_hours"\n        )',
        'self._batch_window_hours = config.getint(\n            "replay.streaming", "batch_window_hours"\n        )'
    )
    content = content.replace(
        'self._snapshot_mode = config.get("replay", "snapshot_mode")',
        'self._snapshot_mode = config.get("replay.streaming", "snapshot_mode")'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_projector_reset():
    """Fix Bug C: batch_totals not reset between windows."""
    path = "/app/runtime/projector.py"
    with open(path, "r") as f:
        content = f.read()
    old_code = '    def _process_batch(self, batch_events):\n        """Process a single batch of events and update projections."""'
    new_code = '    def _process_batch(self, batch_events):\n        """Process a single batch of events and update projections."""\n        self._batch_totals = {}'
    content = content.replace(old_code, new_code)
    with open(path, "w") as f:
        f.write(content)


def patch_sorter():
    """Fix Bug D: sort key missing stream_id for deterministic ordering."""
    path = "/app/runtime/sorter.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'key=lambda e: (e["timestamp"], e["sequence"])',
        'key=lambda e: (e["timestamp"], e["stream_id"], e["sequence"])'
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_filter()
    patch_projector_section()
    patch_projector_reset()
    patch_sorter()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_replay import main as run_main
    run_main()


if __name__ == "__main__":
    main()
