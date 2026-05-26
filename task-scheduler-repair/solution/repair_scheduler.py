#!/usr/bin/env python3
"""Repair script for task scheduler engine. Patches all defects and re-runs."""
import os
import sys


def patch_loader():
    """Fix Bug A: strip whitespace from comma-split worker list."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._active_workers = set(raw_workers.split(","))',
        'self._active_workers = set(w.strip() for w in raw_workers.split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_batch_scheduler():
    """Fix Bug B: read batch_capacity from scheduling.precise section."""
    path = "/app/runtime/batch_scheduler.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._batch_capacity = self._config.getint("scheduling", "batch_capacity")',
        'self._batch_capacity = self._config.getint("scheduling.precise", "batch_capacity")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_resource_tracker():
    """Fix Bug C: compute per-batch snapshots independently, not cumulative."""
    path = "/app/runtime/resource_tracker.py"
    with open(path, "r") as f:
        content = f.read()

    old_code = '''        batch_snapshots = []
        running_totals = {}

        for batch in batches:
            for job_id in batch["jobs"]:
                info = job_lookup.get(job_id, {})
                qid = info.get("queue_id", "unknown")
                units = info.get("resource_units", 0)
                running_totals[qid] = running_totals.get(qid, 0) + units

            # Snapshot records the running total at this point
            batch_snapshots.append(dict(running_totals))

        # Final per-type totals from the last snapshot
        final_totals = batch_snapshots[-1] if batch_snapshots else {}'''

    new_code = '''        batch_snapshots = []
        final_totals = {}

        for batch in batches:
            batch_resources = {}
            for job_id in batch["jobs"]:
                info = job_lookup.get(job_id, {})
                qid = info.get("queue_id", "unknown")
                units = info.get("resource_units", 0)
                batch_resources[qid] = batch_resources.get(qid, 0) + units
                final_totals[qid] = final_totals.get(qid, 0) + units

            # Snapshot records only this batch's allocation
            batch_snapshots.append(batch_resources)'''

    content = content.replace(old_code, new_code)

    with open(path, "w") as f:
        f.write(content)


def patch_priority_scorer():
    """Fix Bug D: add queue_id as tiebreaker in sort key."""
    path = "/app/runtime/priority_scorer.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'key=lambda j: (-j["priority_score"], j["submitted_at"], j["seq"])',
        'key=lambda j: (-j["priority_score"], j["submitted_at"], j["queue_id"], j["seq"])'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_deadline_checker():
    """Fix Bug E: remove off-by-one in batch duration calculation."""
    path = "/app/runtime/deadline_checker.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "batch_duration = self._deadline_window * batch[\"total_resource_units\"] + 1",
        "batch_duration = self._deadline_window * batch[\"total_resource_units\"]"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_batch_scheduler()
    patch_resource_tracker()
    patch_priority_scorer()
    patch_deadline_checker()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_scheduler import main as run_main
    run_main()


if __name__ == "__main__":
    main()
