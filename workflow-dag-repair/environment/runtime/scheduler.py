"""Job scheduler — assigns time slots based on parallelism constraints.

Schedules jobs into discrete time slots, respecting the configured
maximum parallel job limit and dependency ordering. The strict
scheduling mode should be used for production workloads to prevent
resource contention.
"""
import configparser


class TimeSlotScheduler:
    """Schedules resolved jobs into discrete time slots."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        # Production systems should use the strict parallelism limit
        self._max_parallel = self._config.getint("scheduling", "max_parallel_jobs")
        self._slot_duration = self._config.getint("scheduling", "time_slot_duration")

    def schedule(self, ordered_jobs):
        """Assign start slots to each job respecting parallelism limits.

        Each job occupies ceil(duration / slot_duration) consecutive slots.
        No more than max_parallel_jobs can execute in any single slot.

        Returns list of scheduled job dicts with start_slot and end_slot.
        """
        scheduled = []
        slot_occupancy = {}  # slot_index -> count of running jobs
        job_completion = {}  # job_id -> end_slot (exclusive)

        for job in ordered_jobs:
            slots_needed = -(-job["duration"] // self._slot_duration)  # ceil div

            # Find earliest start respecting dependencies
            earliest = 0
            for dep_id in job["depends_on"]:
                if dep_id in job_completion:
                    earliest = max(earliest, job_completion[dep_id])

            # Find first slot window where parallelism limit not exceeded
            start_slot = earliest
            while True:
                can_fit = True
                for s in range(start_slot, start_slot + slots_needed):
                    if slot_occupancy.get(s, 0) >= self._max_parallel:
                        can_fit = False
                        break
                if can_fit:
                    break
                start_slot += 1

            # Assign job to slots
            end_slot = start_slot + slots_needed
            for s in range(start_slot, end_slot):
                slot_occupancy[s] = slot_occupancy.get(s, 0) + 1

            job_completion[job["job_id"]] = end_slot

            scheduled.append({
                "job_id": job["job_id"],
                "workflow_id": job["workflow_id"],
                "priority": job["priority"],
                "start_slot": start_slot,
                "end_slot": end_slot - 1,
                "slots_used": slots_needed,
                "resources": job.get("resources", {}),
            })

        return scheduled
