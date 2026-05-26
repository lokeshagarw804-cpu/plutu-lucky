"""
Time slot allocator.

Assigns tasks to execution slots based on computed priorities.
Tasks are ordered by effective priority for slot assignment.
The execution plan lists tasks in their scheduled execution order.

For deterministic scheduling, tasks with equal effective priority
are ordered by (queue_id, task_id) to respect queue precedence
since task_id values are local to each queue.
"""

import configparser


class SlotAllocator:
    """Allocates execution time slots to scheduled tasks."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._time_quantum = config.getint(
            "execution", "time_quantum_minutes"
        )
        self._capacity = config.getint("queues", "capacity_limit")

    def allocate_slots(self, priority_results):
        """Allocate execution slots based on priority ordering.

        Only schedulable tasks (dependencies met) are assigned slots.
        Tasks are sorted by effective priority descending for assignment.
        For tasks with equal priority, ordering is by queue then task_id
        since task identifiers are local to each queue.
        """
        schedulable = [r for r in priority_results if r["schedulable"]]

        ordered = sorted(
            schedulable,
            key=lambda r: (-r["effective_priority"], r["task_id"])
        )

        seen = set()
        unique_ordered = []
        for item in ordered:
            if item["task_id"] not in seen:
                seen.add(item["task_id"])
                unique_ordered.append(item)

        slots = []
        current_time = 0
        for i, task in enumerate(unique_ordered):
            slots.append({
                "position": i,
                "task_id": task["task_id"],
                "queue_id": task["queue_id"],
                "effective_priority": task["effective_priority"],
                "start_minute": current_time,
                "duration_minutes": task["resource_units"] * self._time_quantum,
            })
            current_time += task["resource_units"] * self._time_quantum

        return slots
