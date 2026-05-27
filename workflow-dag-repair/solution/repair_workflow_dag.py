#!/usr/bin/env python3
"""Repair script for workflow DAG execution engine."""
import os
import sys


def patch_tracker():
    """Fix resource pool name parsing and peak calculation."""
    path = "/app/runtime/tracker.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug A: strip whitespace from pool names when parsing config
    content = content.replace(
        'self._pools = set(raw_pools.split(","))',
        'self._pools = set(p.strip() for p in raw_pools.split(","))'
    )

    # Fix Bug A part 2: strip pool names for limits dict keys too
    content = content.replace(
        'pool_names = list(raw_pools.split(","))',
        'pool_names = [p.strip() for p in raw_pools.split(",")]'
    )

    # Fix Bug C: change sum accumulation to max (peak per slot)
    content = content.replace(
        "peak_usage[pool] += slot_usage[slot][pool]",
        "if slot_usage[slot][pool] > peak_usage[pool]:\n                    peak_usage[pool] = slot_usage[slot][pool]"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_scheduler():
    """Fix config section for parallelism limit."""
    path = "/app/runtime/scheduler.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug B: read from scheduling.strict instead of scheduling
    content = content.replace(
        'self._max_parallel = self._config.getint("scheduling", "max_parallel_jobs")',
        'self._max_parallel = self._config.getint("scheduling.strict", "max_parallel_jobs")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_resolver():
    """Fix sort key to include workflow_id for deterministic ordering."""
    path = "/app/runtime/resolver.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug D: add workflow_id as tiebreaker in both sort calls
    content = content.replace(
        'all_jobs[jid]["submit_time"],\n        ))',
        'all_jobs[jid]["submit_time"],\n            all_jobs[jid]["workflow_id"],\n        ))'
    )
    content = content.replace(
        'all_jobs[jid]["submit_time"],\n            ))',
        'all_jobs[jid]["submit_time"],\n                all_jobs[jid]["workflow_id"],\n            ))'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_tracker()
    patch_scheduler()
    patch_resolver()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_workflow import main as run_main
    run_main()


if __name__ == "__main__":
    main()
