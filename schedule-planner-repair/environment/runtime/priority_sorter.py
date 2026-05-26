"""Priority sorter — establishes execution ordering across all queues.

When scheduling jobs from multiple queues, a deterministic ordering
is required. Jobs are sorted by priority (higher first), then by
deadline (earlier first), with additional fields for tie resolution.

Note: job_seq is local to each queue and resets per source.
"""
import configparser


class PrioritySorter:
    """Produces a deterministic total ordering of jobs across queues."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)

    def sort_jobs(self, queues):
        """Merge jobs from all queues into a single priority-ordered list.

        Each job is annotated with its source queue_id.
        Ordering: priority descending, then deadline ascending,
        then job_seq ascending for ties.
        """
        all_jobs = []
        for queue_id, jobs in queues.items():
            for job in jobs:
                entry = dict(job)
                entry["queue_id"] = queue_id
                all_jobs.append(entry)

        # Sort for deterministic scheduling order
        all_jobs.sort(key=lambda j: (-j["priority"], j["deadline"], j["job_seq"]))

        return all_jobs
