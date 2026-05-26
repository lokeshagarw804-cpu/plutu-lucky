#!/usr/bin/env python3
"""Repair script for event projector. Patches all defects and re-runs."""
import os
import sys


def patch_loader():
    """Fix Bug A: strip whitespace from comma-split aggregate type list."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._active_types = set(raw_types.split(","))',
        'self._active_types = set(t.strip() for t in raw_types.split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_projector():
    """Fix Bug B: read snapshot_interval from projection.materialized section."""
    path = "/app/runtime/projector.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._snapshot_interval = self._config.getint(\n            "projection", "snapshot_interval"\n        )',
        'self._snapshot_interval = self._config.getint(\n            "projection.materialized", "snapshot_interval"\n        )'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_projector_accumulation():
    """Fix Bug C: reset interval counts per snapshot instead of accumulating."""
    path = "/app/runtime/projector.py"
    with open(path, "r") as f:
        content = f.read()

    old_code = '''        snapshots = []
        # Running counters for projection
        running_counts = {}
        interval_start = 0

        for idx, event in enumerate(replay_sequence):
            agg_id = event["aggregate_id"]
            running_counts[agg_id] = running_counts.get(agg_id, 0) + 1

            # Take snapshot at interval boundary
            if (idx + 1) % self._snapshot_interval == 0:
                snapshots.append({
                    "snapshot_id": len(snapshots),
                    "events_processed": idx + 1,
                    "interval_start": interval_start,
                    "interval_end": idx,
                    "state": dict(running_counts),
                })
                interval_start = idx + 1

        # Final snapshot for remaining events
        if interval_start <= len(replay_sequence) - 1:
            snapshots.append({
                "snapshot_id": len(snapshots),
                "events_processed": len(replay_sequence),
                "interval_start": interval_start,
                "interval_end": len(replay_sequence) - 1,
                "state": dict(running_counts),
            })

        return snapshots, running_counts'''

    new_code = '''        snapshots = []
        # Per-interval counters for projection
        interval_counts = {}
        total_counts = {}
        interval_start = 0

        for idx, event in enumerate(replay_sequence):
            agg_id = event["aggregate_id"]
            interval_counts[agg_id] = interval_counts.get(agg_id, 0) + 1
            total_counts[agg_id] = total_counts.get(agg_id, 0) + 1

            # Take snapshot at interval boundary
            if (idx + 1) % self._snapshot_interval == 0:
                snapshots.append({
                    "snapshot_id": len(snapshots),
                    "events_processed": idx + 1,
                    "interval_start": interval_start,
                    "interval_end": idx,
                    "state": dict(interval_counts),
                })
                interval_start = idx + 1
                interval_counts = {}

        # Final snapshot for remaining events
        if interval_start <= len(replay_sequence) - 1:
            snapshots.append({
                "snapshot_id": len(snapshots),
                "events_processed": len(replay_sequence),
                "interval_start": interval_start,
                "interval_end": len(replay_sequence) - 1,
                "state": dict(interval_counts),
            })

        return snapshots, total_counts'''

    content = content.replace(old_code, new_code)

    with open(path, "w") as f:
        f.write(content)


def patch_replayer():
    """Fix Bug D: add aggregate_id as tiebreaker in event sort."""
    path = "/app/runtime/replayer.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'all_events.sort(key=lambda e: (e["timestamp"], e["seq"]))',
        'all_events.sort(key=lambda e: (e["timestamp"], e["aggregate_id"], e["seq"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_deduplicator():
    """Fix Bug E: correct dedup window boundary from window+1 to window."""
    path = "/app/runtime/deduplicator.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "window_start = max(0, len(seen_windows) - (self._window + 1))",
        "window_start = max(0, len(seen_windows) - self._window)"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_projector()
    patch_projector_accumulation()
    patch_replayer()
    patch_deduplicator()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_projector import main as run_main
    run_main()


if __name__ == "__main__":
    main()
