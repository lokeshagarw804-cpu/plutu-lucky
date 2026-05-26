#!/usr/bin/env python3
"""Repair script for the task scheduling system."""
import os
import sys


def patch_queue_filter():
    """Fix Bug A: priority_queues parsing does not strip whitespace."""
    path = "/app/runtime/queue_filter.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._active_queues = set(raw_queues.split(","))',
        'self._active_queues = set(q.strip() for q in raw_queues.split(","))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_priority_section():
    """Fix Bug B: priority engine reads from wrong config section."""
    path = "/app/runtime/priority_engine.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._aging_factor = config.getfloat("scheduling", "aging_factor")',
        'self._aging_factor = config.getfloat("scheduling.weighted", "aging_factor")'
    )
    content = content.replace(
        'self._deadline_weight = config.getfloat(\n            "scheduling", "deadline_weight"\n        )',
        'self._deadline_weight = config.getfloat(\n            "scheduling.weighted", "deadline_weight"\n        )'
    )
    content = content.replace(
        'self._dependency_boost = config.getint(\n            "scheduling", "dependency_boost"\n        )',
        'self._dependency_boost = config.getint(\n            "scheduling.weighted", "dependency_boost"\n        )'
    )
    content = content.replace(
        'self._max_rounds = config.getint("scheduling", "max_rounds")',
        'self._max_rounds = config.getint("scheduling.weighted", "max_rounds")'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_priority_accumulation():
    """Fix Bug C: priority history accumulates across rounds."""
    path = "/app/runtime/priority_engine.py"
    with open(path, "r") as f:
        content = f.read()
    old_code = '''        contribution = base + aging + urgency + dep_boost
        self._priority_history[tid] = (
            self._priority_history.get(tid, 0.0) + contribution
        )

        return round(self._priority_history[tid], 4)'''
    new_code = '''        contribution = base + aging + urgency + dep_boost

        return round(contribution, 4)'''
    content = content.replace(old_code, new_code)
    with open(path, "w") as f:
        f.write(content)


def patch_slot_sort():
    """Fix Bug D: slot allocation sort missing queue_id tiebreaker."""
    path = "/app/runtime/slot_allocator.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'key=lambda r: (-r["effective_priority"], r["task_id"])',
        'key=lambda r: (-r["effective_priority"], r["queue_id"], r["task_id"])'
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_queue_filter()
    patch_priority_section()
    patch_priority_accumulation()
    patch_slot_sort()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_scheduler import main as run_main
    run_main()


if __name__ == "__main__":
    main()
