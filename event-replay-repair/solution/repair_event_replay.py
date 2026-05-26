#!/usr/bin/env python3
"""Repair script for the event replay materialization system.

Patches the four defects in the runtime and re-runs the system to produce
correct output.
"""
import os
import sys


def patch_loader():
    """Fix Bug A: config comma-split strips whitespace from stream names."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._allowed = set(raw_streams.split(","))',
        'self._allowed = set(item.strip() for item in raw_streams.split(","))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_projector_config():
    """Fix Bug B: projector reads wrong config section for batch_size."""
    path = "/app/runtime/projector.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._batch_size = self._config.getint("projection", "batch_size")',
        'self._batch_size = self._config.getint("projection.incremental", "batch_size")'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_projector_accumulation():
    """Fix Bug C: projector accumulates across batches instead of last-write-wins."""
    path = "/app/runtime/projector.py"
    with open(path, "r") as f:
        content = f.read()
    old_block = '''                for key in ["total_amount", "payment_amount", "refund_amount", "event_count"]:
                    if key in state:
                        agg[key] += state[key]'''
    new_block = '''                for key in ["total_amount", "payment_amount", "refund_amount", "event_count"]:
                    if key in state:
                        agg[key] = state[key]'''
    content = content.replace(old_block, new_block)
    with open(path, "w") as f:
        f.write(content)


def patch_correlator_sort():
    """Fix Bug D: sort tiebreaker must include stream_id for deterministic ordering."""
    path = "/app/runtime/correlator.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'key=lambda e: (parse_ts(e["timestamp"]), e["seq"])',
        'key=lambda e: (parse_ts(e["timestamp"]), e["stream_id"], e["seq"])'
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_projector_config()
    patch_projector_accumulation()
    patch_correlator_sort()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_replay import main as run_main
    run_main()


if __name__ == "__main__":
    main()
