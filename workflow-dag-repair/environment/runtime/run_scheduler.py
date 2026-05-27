"""Workflow DAG scheduler — main entry point.

Orchestrates the full scheduling cycle: load graph, resolve dependencies,
compute priorities, build schedule, and write audit output.
"""
import sys
import os

from runtime.loader import WorkflowLoader
from runtime.resolver import DependencyResolver
from runtime.prioritizer import PriorityCalculator
from runtime.scheduler import ExecutionScheduler
from runtime.audit_writer import AuditWriter


def main():
    config_path = "/app/runtime/config.ini"

    # Load workflow data
    loader = WorkflowLoader(config_path)
    graph = loader.load_graph()
    resources = loader.load_resources()
    overrides = loader.load_overrides()
    priority_weights = loader.get_priority_weights()

    print(f"Loaded workflow: {graph['workflow_id']}")
    print(f"Nodes: {len(graph['nodes'])}")
    print(f"Priority weights: {priority_weights}")

    # Initialize components
    resolver = DependencyResolver(graph)
    prioritizer = PriorityCalculator(graph, priority_weights, overrides)
    scheduler = ExecutionScheduler(config_path, resolver, prioritizer, graph)

    # Build schedule
    schedule = scheduler.build_schedule()

    print(f"Schedule built: {len(schedule)} slots")
    total_scheduled = sum(len(s) for s in schedule)
    print(f"Nodes scheduled: {total_scheduled}/{len(graph['nodes'])}")

    # Write output
    output_dir = "/app/runtime/output"
    writer = AuditWriter(output_dir)
    writer.write_schedule(schedule, prioritizer, graph, scheduler)

    print(f"Output written to {output_dir}")


if __name__ == "__main__":
    main()
