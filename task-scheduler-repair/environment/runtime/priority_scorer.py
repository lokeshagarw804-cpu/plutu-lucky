"""Priority scorer — computes scheduling priority for each job.

Uses weighted scoring based on urgency, resource requirements, and
job age. The scoring produces a composite priority value that the
batch scheduler uses to determine execution order.

Jobs are sorted by priority descending. For jobs with the same
computed priority, ordering should be deterministic using the
queue_id and then seq number within that queue as tiebreakers.
"""
import configparser


# Note: seq is local to each queue — it does not provide global ordering
REFERENCE_TIME = 1700000500


class PriorityScorer:
    """Computes priority scores for jobs using weighted factors."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._w_urgency = self._config.getfloat("priorities", "weight_urgency")
        self._w_resource = self._config.getfloat("priorities", "weight_resource")
        self._w_age = self._config.getfloat("priorities", "weight_age")

    def score_jobs(self, queues):
        """Score all jobs across all queues and return sorted list.

        Each job gets a composite priority score. Jobs are sorted by
        score descending so highest-priority jobs come first.
        """
        scored_jobs = []

        for queue_id, queue_data in queues.items():
            for job in queue_data["jobs"]:
                score = self._compute_score(job)
                scored_jobs.append({
                    "job_id": job["job_id"],
                    "queue_id": queue_id,
                    "priority_score": round(score, 4),
                    "submitted_at": job["submitted_at"],
                    "deadline": job["deadline"],
                    "resource_units": job["resource_units"],
                    "urgency": job["urgency"],
                    "seq": job["seq"],
                })

        # Sort by priority score descending
        scored_jobs.sort(
            key=lambda j: (-j["priority_score"], j["submitted_at"], j["seq"])
        )

        return scored_jobs

    def _compute_score(self, job):
        """Compute weighted priority score for a single job.

        Components:
        - urgency: raw urgency value (1-10) normalized to 0-1
        - resource: inverse of resource_units (smaller jobs get slight boost)
        - age: how long the job has been waiting relative to reference time
        """
        urgency_norm = job["urgency"] / 10.0
        resource_norm = 1.0 / job["resource_units"]
        age_seconds = REFERENCE_TIME - job["submitted_at"]
        age_norm = min(age_seconds / 500.0, 1.0)

        return (
            self._w_urgency * urgency_norm
            + self._w_resource * resource_norm
            + self._w_age * age_norm
        )
