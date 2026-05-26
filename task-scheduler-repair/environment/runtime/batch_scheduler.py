"""Batch scheduler — groups jobs into execution batches.

Takes priority-sorted jobs and assigns them to sequential batches,
respecting the batch resource capacity limit. Each batch can hold
jobs up to the configured capacity in total resource units.

The batch capacity is controlled by the scheduling.precise section
which provides fine-tuned values for the production scheduler.
"""
import configparser


class BatchScheduler:
    """Assigns priority-sorted jobs to resource-bounded execution batches."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        # Batch capacity determines max resource units per batch
        self._batch_capacity = self._config.getint("scheduling", "batch_capacity")
        self._max_concurrent = self._config.getint("scheduling", "max_concurrent")

    def schedule_batches(self, scored_jobs):
        """Assign jobs to batches respecting capacity constraints.

        Jobs arrive in priority order. Each batch fills until adding
        the next job would exceed capacity, then a new batch starts.
        Returns list of batch dicts with assigned jobs and utilization.
        """
        batches = []
        current_batch = []
        current_load = 0
        batch_idx = 0

        for job in scored_jobs:
            if current_load + job["resource_units"] > self._batch_capacity:
                if current_batch:
                    batches.append(self._finalize_batch(
                        batch_idx, current_batch, current_load
                    ))
                    batch_idx += 1
                current_batch = [job]
                current_load = job["resource_units"]
            else:
                current_batch.append(job)
                current_load += job["resource_units"]

        # Final batch
        if current_batch:
            batches.append(self._finalize_batch(
                batch_idx, current_batch, current_load
            ))

        return batches

    def _finalize_batch(self, idx, jobs, load):
        """Create batch record with utilization metrics."""
        return {
            "batch_id": idx,
            "job_count": len(jobs),
            "total_resource_units": load,
            "utilization": round(load / self._batch_capacity, 4),
            "jobs": [j["job_id"] for j in jobs],
            "capacity": self._batch_capacity,
        }
