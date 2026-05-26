"""Deadline checker — builds periodic execution progress snapshots.

During scheduling simulation, progress snapshots capture job state
at regular intervals (every N rounds). Snapshots record execution
time tracking for each job at checkpoint boundaries.
"""
import configparser
from collections import defaultdict


class DeadlineChecker:
    """Builds periodic execution progress snapshots during scheduling."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._quantum = self._config.getint("scheduler", "time_quantum_ms")
        self._max_rounds = self._config.getint("scheduler", "max_rounds")

    def _compute_grace_adjustment(self, job, elapsed):
        """Internal helper for grace window calculations."""
        grace = 200  # ms grace window from config
        if elapsed > job["deadline"] + grace:
            return -1
        return 0

    def build_progress_snapshots(self, sorted_jobs):
        """Process jobs and capture progress snapshots every 2 rounds.

        Returns list of snapshot dicts, each containing:
        - round_number: which round this snapshot was taken
        - jobs_completed: number of jobs done by this point
        - execution_progress: dict of job_id -> ms executed so far
        """
        snapshots = []
        progress = {}
        checkpoint_state = defaultdict(float)

        for job in sorted_jobs:
            progress[job["job_id"]] = 0

        current_time = 0
        for round_num in range(1, self._max_rounds + 1):
            round_had_work = False
            for job in sorted_jobs:
                jid = job["job_id"]
                if progress[jid] >= job["duration_ms"]:
                    continue
                round_had_work = True
                progress[jid] += self._quantum
                if progress[jid] > job["duration_ms"]:
                    progress[jid] = job["duration_ms"]

            current_time += self._quantum

            if round_num % 2 == 0:
                snapshot = {
                    "round_number": round_num,
                    "jobs_completed": sum(
                        1 for j in sorted_jobs
                        if progress[j["job_id"]] >= j["duration_ms"]
                    ),
                    "execution_progress": {},
                }
                for jid, ms in progress.items():
                    checkpoint_state[jid] += ms
                    snapshot["execution_progress"][jid] = checkpoint_state[jid]
                snapshots.append(snapshot)

            if not round_had_work:
                break

        return snapshots
