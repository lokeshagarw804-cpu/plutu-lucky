#!/usr/bin/env python3
"""Repair script for workflow DAG scheduler. Patches bugs and re-runs."""
import os
import sys


def patch_loader():
    """Fix Bug A: strip whitespace from priority level names."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'levels = set(raw_levels.split(","))',
        'levels = set(l.strip() for l in raw_levels.split(","))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_scheduler():
    """Fix Bug B: read max_parallelism from scheduler.constrained section."""
    path = "/app/runtime/scheduler.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._max_parallel = self._config.getint("scheduler", "max_parallelism")',
        'self._max_parallel = self._config.getint("scheduler.constrained", "max_parallelism")'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_prioritizer():
    """Fix Bug C: use max() for critical path cost, not sum.
    Fix Bug D: add depth to sort tiebreaker.
    """
    path = "/app/runtime/prioritizer.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug C: critical path should use max, not accumulate
    old_cost = """        # Accumulate cost from all predecessor chains
        total = 0
        for dep in deps:
            dep_cost = self._get_critical_cost(dep) + self._nodes[dep]["cost"]
            total += dep_cost
        return total"""
    new_cost = """        # Critical path: take the maximum (bottleneck) predecessor chain
        return max(
            self._get_critical_cost(dep) + self._nodes[dep]["cost"]
            for dep in deps
        )"""
    content = content.replace(old_cost, new_cost)

    # Fix Bug D: add depth descending to sort tiebreaker
    old_sort = '            key=lambda nid: (-self.get_effective_priority(nid), nid)'
    new_sort = '            key=lambda nid: (-self.get_effective_priority(nid), -self._depths.get(nid, 0), nid)'
    content = content.replace(old_sort, new_sort)

    with open(path, "w") as f:
        f.write(content)


def patch_resolver():
    """Fix Bug E: check for 'completed' status matching what mark_completed sets."""
    path = "/app/runtime/resolver.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._status[dep] == "done"',
        'self._status[dep] == "completed"'
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_scheduler()
    patch_prioritizer()
    patch_resolver()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_scheduler import main as run_main
    run_main()


if __name__ == "__main__":
    main()
