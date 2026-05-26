#!/usr/bin/env python3
"""Repair script for preemptive priority scheduling engine."""
import os
import sys


def patch_queue_loader():
    """Fix Bug A: strip whitespace from comma-separated queue names."""
    path = "/app/runtime/queue_loader.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._active = set(raw_queues.split(","))',
        'self._active = set(q.strip() for q in raw_queues.split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_plan_validator():
    """Fix Bug B: read validation_tolerance_ms from correct config section."""
    path = "/app/runtime/plan_validator.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._tolerance = self._config.getint(\n            "scheduler", "validation_tolerance_ms"\n        )',
        'self._tolerance = self._config.getint(\n            "scheduler.validation", "validation_tolerance_ms"\n        )'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_deadline_checker():
    """Fix Bug C: record point-in-time progress instead of accumulating."""
    path = "/app/runtime/deadline_checker.py"
    with open(path, "r") as f:
        content = f.read()

    old_code = """                for jid, ms in progress.items():
                    cumulative[jid] += ms
                    snapshot["execution_progress"][jid] = cumulative[jid]"""

    new_code = """                for jid, ms in progress.items():
                    snapshot["execution_progress"][jid] = ms"""

    content = content.replace(old_code, new_code)

    with open(path, "w") as f:
        f.write(content)


def patch_priority_sorter():
    """Fix Bug D: add queue_id to sort key for deterministic ordering."""
    path = "/app/runtime/priority_sorter.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'all_jobs.sort(key=lambda j: (-j["priority"], j["deadline"], j["job_seq"]))',
        'all_jobs.sort(key=lambda j: (-j["priority"], j["deadline"], j["queue_id"], j["job_seq"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_queue_loader()
    patch_plan_validator()
    patch_deadline_checker()
    patch_priority_sorter()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_scheduler import main as run_main
    run_main()


if __name__ == "__main__":
    main()
