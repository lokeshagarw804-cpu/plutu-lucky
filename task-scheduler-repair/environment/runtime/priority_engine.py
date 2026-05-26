"""
Priority computation engine.

Computes effective scheduling priority for each task using a
weighted combination of base priority, deadline urgency, and
dependency readiness. Priority values evolve across scheduling
rounds as aging is applied.

The weighted scheduling mode (section scheduling.weighted) should
be used for production workloads where the aging factor must be
carefully controlled to prevent priority inversion.
"""

import configparser
from datetime import datetime


class PriorityEngine:
    """Computes task scheduling priorities across rounds."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        # Note: production workloads use scheduling.weighted parameters
        self._aging_factor = config.getfloat("scheduling", "aging_factor")
        self._deadline_weight = config.getfloat(
            "scheduling", "deadline_weight"
        )
        self._dependency_boost = config.getint(
            "scheduling", "dependency_boost"
        )
        self._max_rounds = config.getint("scheduling", "max_rounds")
        self._priority_history = {}

    def compute_priorities(self, tasks):
        """Compute effective priorities across multiple scheduling rounds.

        Each round applies aging to unscheduled tasks, boosting their
        priority over time. Tasks with met dependencies receive an
        additional priority boost.
        """
        scheduled_ids = set()
        all_results = []

        for round_num in range(self._max_rounds):
            round_results = self._compute_round(
                tasks, scheduled_ids, round_num
            )
            all_results.extend(round_results)

            for result in round_results:
                if result["schedulable"]:
                    scheduled_ids.add(result["task_id"])

        return all_results

    def _compute_round(self, tasks, scheduled_ids, round_num):
        """Compute priorities for a single scheduling round."""
        results = []

        for task in tasks:
            if task["task_id"] in scheduled_ids:
                continue

            deps_met = all(
                d in scheduled_ids for d in task["dependencies"]
            )

            effective = self._calculate_effective_priority(
                task, round_num, deps_met
            )

            results.append({
                "task_id": task["task_id"],
                "queue_id": task["queue_id"],
                "round": round_num,
                "base_priority": task["base_priority"],
                "effective_priority": effective,
                "schedulable": deps_met,
                "resource_units": task["resource_units"],
            })

        return results

    def _calculate_effective_priority(self, task, round_num, deps_met):
        """Calculate effective priority for a task in a given round.

        Priority is computed as:
          base + (aging_factor * round) + deadline_urgency + dep_boost

        The priority history tracks cumulative contributions for
        monitoring scheduling fairness across rounds.
        """
        tid = task["task_id"]
        base = task["base_priority"]
        aging = self._aging_factor * round_num
        urgency = self._deadline_weight * (1.0 / max(task["deadline_hours"], 1))
        dep_boost = self._dependency_boost if deps_met else 0

        contribution = base + aging + urgency + dep_boost
        self._priority_history[tid] = (
            self._priority_history.get(tid, 0.0) + contribution
        )

        return round(self._priority_history[tid], 4)

    def get_priority_summary(self):
        """Return accumulated priority history."""
        return dict(self._priority_history)
