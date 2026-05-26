"""Task scheduler engine — main entry point.

Orchestrates job scheduling: loads queues, scores priorities, assigns
batches, checks deadlines, and generates utilization report. Produces
execution manifest and resource utilization report as output.
"""
import json
import os

from runtime.loader import QueueLoader
from runtime.priority_scorer import PriorityScorer
from runtime.batch_scheduler import BatchScheduler
from runtime.deadline_checker import DeadlineChecker
from runtime.resource_tracker import ResourceTracker


REFERENCE_TIME = 1700000500


def main():
    config_path = "/app/runtime/config.ini"

    # Load job queues (only active worker types)
    loader = QueueLoader(config_path)
    queues = loader.load_queues()

    # Score and sort jobs by priority
    scorer = PriorityScorer(config_path)
    scored_jobs = scorer.score_jobs(queues)

    # Assign to execution batches
    scheduler = BatchScheduler(config_path)
    batches = scheduler.schedule_batches(scored_jobs)

    # Check deadline compliance
    checker = DeadlineChecker(config_path)
    timing = checker.check_deadlines(batches, REFERENCE_TIME)

    # Compute resource utilization
    tracker = ResourceTracker()
    utilization = tracker.compute_utilization(batches, scored_jobs)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    # Execution manifest
    manifest = {
        "total_jobs": len(scored_jobs),
        "total_batches": len(batches),
        "batches": batches,
        "scheduling_order": [j["job_id"] for j in scored_jobs],
        "timing": timing,
    }
    with open(os.path.join(output_dir, "execution_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    # Utilization report
    report = {
        "total_resource_units": sum(
            utilization["per_type_totals"].values()
        ),
        "per_type_totals": utilization["per_type_totals"],
        "batch_count": utilization["batch_count"],
        "batch_snapshots": utilization["batch_snapshots"],
        "active_worker_types": sorted(utilization["per_type_totals"].keys()),
    }
    with open(os.path.join(output_dir, "utilization_report.json"), "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
