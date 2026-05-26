"""
Execution plan writer.

Generates the final execution plan, schedule matrix, and
processing summary output files.
"""

import json
import os
import configparser


class PlanWriter:
    """Writes scheduling output files."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._plan_path = config.get("execution", "output_path")
        self._schedule_path = config.get("execution", "schedule_path")
        self._summary_path = config.get("execution", "summary_path")

    def write_outputs(self, slots, priority_results, tasks):
        """Write all output files."""
        plan = self._build_plan(slots)
        schedule = self._build_schedule(priority_results)
        summary = self._build_summary(slots, priority_results, tasks)

        self._write_json(self._plan_path, plan)
        self._write_json(self._schedule_path, schedule)
        self._write_json(self._summary_path, summary)

        return plan, schedule, summary

    def _build_plan(self, slots):
        """Build the execution plan from allocated slots."""
        return {
            "total_scheduled": len(slots),
            "entries": slots,
            "total_duration_minutes": sum(
                s["duration_minutes"] for s in slots
            ),
        }

    def _build_schedule(self, priority_results):
        """Build schedule matrix from priority computations."""
        by_round = {}
        for result in priority_results:
            r = result["round"]
            if r not in by_round:
                by_round[r] = []
            by_round[r].append({
                "task_id": result["task_id"],
                "queue_id": result["queue_id"],
                "effective_priority": result["effective_priority"],
                "schedulable": result["schedulable"],
            })
        return {
            "rounds": by_round,
            "total_evaluations": len(priority_results),
        }

    def _build_summary(self, slots, priority_results, tasks):
        """Build processing summary."""
        queues = set(t["queue_id"] for t in tasks)
        scheduled_queues = set(s["queue_id"] for s in slots)

        return {
            "total_tasks_input": len(tasks),
            "total_scheduled": len(slots),
            "queues_processed": sorted(queues),
            "queues_in_plan": sorted(scheduled_queues),
            "total_rounds": max(
                (r["round"] for r in priority_results), default=0
            ) + 1,
            "by_queue": {
                q: sum(1 for s in slots if s["queue_id"] == q)
                for q in sorted(scheduled_queues)
            },
        }

    def _write_json(self, path, data):
        """Write data as JSON."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
