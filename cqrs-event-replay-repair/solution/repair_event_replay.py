#!/usr/bin/env python3
"""Repair script for event replay engine. Patches bugs and re-runs."""
import os
import sys


def patch_loader():
    """Fix whitespace handling in active_aggregates parsing."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug A: strip whitespace from split items
    content = content.replace(
        'self._active = set(raw_aggregates.split(","))',
        'self._active = set(s.strip() for s in raw_aggregates.split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_batcher():
    """Fix batch size to read from correct config section."""
    path = "/app/runtime/batcher.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug B: read from replay.strict instead of replay
    content = content.replace(
        'self._batch_size = self._config.getint("replay", "batch_size")',
        'self._batch_size = self._config.getint("replay.strict", "batch_size")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_materializer():
    """Fix snapshot mode to read from correct config section."""
    path = "/app/runtime/materializer.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug C: read snapshot_mode from replay.strict (latest) not replay (cumulative)
    content = content.replace(
        'self._snapshot_mode = self._config.get("replay", "snapshot_mode")',
        'self._snapshot_mode = self._config.get("replay.strict", "snapshot_mode")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_sequencer():
    """Fix event ordering to include stream_id for deterministic sort."""
    path = "/app/runtime/sequencer.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug D: add stream_id to sort key for cross-stream determinism
    content = content.replace(
        'merged.sort(key=lambda e: (e["timestamp"], e["seq"]))',
        'merged.sort(key=lambda e: (e["timestamp"], e["stream_id"], e["seq"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_batcher()
    patch_materializer()
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
