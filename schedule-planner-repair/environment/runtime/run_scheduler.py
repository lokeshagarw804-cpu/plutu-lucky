"""Task scheduler — main entry point.

Orchestrates the full scheduling process: loads job queues,
sorts by priority and deadline, executes in rounds, builds
progress snapshots, and validates consistency.
"""
import json
import os

from runtime.queue_loader import QueueLoader
from runtime.priority_sorter import PrioritySorter
from runtime.executor import Executor
from runtime.deadline_checker import DeadlineChecker
from runtime.plan_validator import PlanValidator


def main():
    config_path = "/app/runtime/config.ini"

    # Load job queues
    loader = QueueLoader(config_path)
    queues = loader.load_queues()

    # Sort by priority and deadline
    sorter = PrioritySorter(config_path)
    sorted_jobs = sorter.sort_jobs(queues)

    # Execute scheduling rounds
    executor = Executor(config_path)
    execution_results = executor.execute(sorted_jobs)

    # Build progress snapshots
    checker = DeadlineChecker(config_path)
    snapshots = checker.build_progress_snapshots(sorted_jobs)

    # Validate consistency
    validator = PlanValidator(config_path)
    report = validator.validate(execution_results, snapshots)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    schedule_output = {
        "total_jobs_scheduled": len(sorted_jobs),
        "total_queues": len(queues),
        "jobs_completed": sum(1 for r in execution_results if r["completed"]),
        "deadlines_met": sum(1 for r in execution_results if r.get("deadline_met")),
        "execution_results": execution_results,
        "queues_loaded": sorted(queues.keys()),
    }
    with open(os.path.join(output_dir, "execution_plan.json"), "w") as f:
        json.dump(schedule_output, f, indent=2)

    snapshot_output = {
        "snapshot_interval_rounds": 2,
        "total_snapshots": len(snapshots),
        "snapshots": snapshots,
    }
    with open(os.path.join(output_dir, "progress_snapshots.json"), "w") as f:
        json.dump(snapshot_output, f, indent=2)

    with open(os.path.join(output_dir, "validation_report.json"), "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
