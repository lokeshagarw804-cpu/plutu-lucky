"""Executor — simulates job execution across scheduling rounds.

Processes the priority-sorted job list in rounds, each round
allocating the configured time quantum to jobs. Tracks per-job
execution progress, completion status, and deadline compliance.
"""
import configparser


class Executor:
    """Simulates round-robin execution with priority scheduling."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._quantum = self._config.getint("scheduler", "time_quantum_ms")
        self._max_rounds = self._config.getint("scheduler", "max_rounds")

    def execute(self, sorted_jobs):
        """Run scheduling simulation across multiple rounds.

        Each round allocates time_quantum_ms to each pending job.
        Jobs complete when their accumulated execution time reaches
        their required duration_ms.

        Returns execution log with per-job completion data.
        """
        job_states = []
        for job in sorted_jobs:
            job_states.append({
                "job_id": job["job_id"],
                "queue_id": job["queue_id"],
                "priority": job["priority"],
                "deadline": job["deadline"],
                "duration_ms": job["duration_ms"],
                "executed_ms": 0,
                "completed": False,
                "completion_round": None,
                "deadline_met": None,
            })

        current_time = 0
        for round_num in range(1, self._max_rounds + 1):
            round_had_work = False
            for state in job_states:
                if state["completed"]:
                    continue
                round_had_work = True
                state["executed_ms"] += self._quantum
                if state["executed_ms"] >= state["duration_ms"]:
                    state["completed"] = True
                    state["completion_round"] = round_num
                    completion_time = current_time + self._quantum
                    state["deadline_met"] = completion_time <= state["deadline"]
            current_time += self._quantum
            if not round_had_work:
                break

        return job_states
