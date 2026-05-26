"""Resource tracker — computes utilization report across batches.

Aggregates resource usage per worker type across all batches to
produce a utilization report. Each batch's resource consumption is
tracked independently — the tracker should report per-batch
snapshots showing only that batch's resources, and total resources
per worker type summed across all batches.
"""


class ResourceTracker:
    """Tracks resource utilization across scheduled batches."""

    def __init__(self):
        self._type_totals = {}

    def compute_utilization(self, batches, scored_jobs):
        """Compute resource utilization per worker type.

        For each batch, computes resource units by the queue_id
        (worker type) of each job in that batch. Each batch snapshot
        should reflect only that batch's resource allocation.

        Reports total resource units allocated per worker type
        across all batches.
        """
        # Build lookup from job_id to queue_id and resource_units
        job_lookup = {}
        for job in scored_jobs:
            job_lookup[job["job_id"]] = {
                "queue_id": job["queue_id"],
                "resource_units": job["resource_units"],
            }

        batch_snapshots = []
        running_totals = {}

        for batch in batches:
            for job_id in batch["jobs"]:
                info = job_lookup.get(job_id, {})
                qid = info.get("queue_id", "unknown")
                units = info.get("resource_units", 0)
                running_totals[qid] = running_totals.get(qid, 0) + units

            # Snapshot records the running total at this point
            batch_snapshots.append(dict(running_totals))

        # Final per-type totals from the last snapshot
        final_totals = batch_snapshots[-1] if batch_snapshots else {}

        return {
            "per_type_totals": final_totals,
            "batch_count": len(batches),
            "batch_snapshots": batch_snapshots,
        }
