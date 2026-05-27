"""Workflow DAG execution engine — main entry point.

Orchestrates the full scheduling process: load workflow definitions,
resolve dependencies, schedule into time slots, track resource
utilization, and generate output reports.
"""
from runtime.loader import WorkflowLoader
from runtime.resolver import DependencyResolver
from runtime.scheduler import TimeSlotScheduler
from runtime.tracker import ResourceTracker
from runtime.reporter import ReportGenerator


def main():
    config_path = "/app/runtime/config.ini"

    # Load workflows
    loader = WorkflowLoader(config_path)
    workflows = loader.load_workflows()

    # Resolve dependencies and ordering
    resolver = DependencyResolver(config_path)
    ordered_jobs = resolver.resolve(workflows)

    # Schedule into time slots
    scheduler = TimeSlotScheduler(config_path)
    scheduled_jobs = scheduler.schedule(ordered_jobs)

    # Track resource utilization
    tracker = ResourceTracker(config_path)
    utilization = tracker.compute_utilization(scheduled_jobs)

    # Generate reports
    output_dir = "/app/runtime/output"
    reporter = ReportGenerator(output_dir)
    reporter.generate(scheduled_jobs, utilization)

    print(f"Scheduled {len(scheduled_jobs)} jobs across {utilization['total_slots']} time slots")
    print(f"Workflows processed: {len(workflows)}")


if __name__ == "__main__":
    main()
