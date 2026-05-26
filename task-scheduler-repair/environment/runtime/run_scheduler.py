"""
Main entry point for the task scheduling system.

Orchestrates the full scheduling process:
1. Load task definitions from queue data files
2. Filter tasks by active priority queues
3. Compute effective priorities across scheduling rounds
4. Allocate execution time slots
5. Write execution plan outputs
"""

from runtime.loader import load_queues
from runtime.queue_filter import QueueFilter
from runtime.priority_engine import PriorityEngine
from runtime.slot_allocator import SlotAllocator
from runtime.plan_writer import PlanWriter


def main():
    """Run the task scheduling process."""
    # Stage 1: Load task queues
    tasks = load_queues()

    # Stage 2: Filter by active queues
    queue_filter = QueueFilter()
    filtered = queue_filter.filter_tasks(tasks)

    # Stage 3: Compute priorities
    engine = PriorityEngine()
    priority_results = engine.compute_priorities(filtered)

    # Stage 4: Allocate slots
    allocator = SlotAllocator()
    slots = allocator.allocate_slots(priority_results)

    # Stage 5: Write outputs
    writer = PlanWriter()
    plan, schedule, summary = writer.write_outputs(
        slots, priority_results, filtered
    )

    print(f"Scheduled {plan['total_scheduled']} tasks")
    print(f"Total duration: {plan['total_duration_minutes']} minutes")
    print(f"Queues: {summary['queues_in_plan']}")
    print(f"Rounds: {summary['total_rounds']}")


if __name__ == "__main__":
    main()
