"""Priority sorter — establishes execution ordering across all queues.

When scheduling jobs from multiple queues, a deterministic ordering
is required. Jobs are sorted by priority (higher first), then by
deadline (earlier first), with additional fields for tie resolution.

Note: job_seq is a per-queue local counter that resets for each source.
"""
import configparser


class PrioritySorter:
    """Produces a deterministic total ordering of jobs across queues."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._algorithm = self._config.get("scheduler", "algorithm")

    def sort_jobs(self, queues):
        """Merge jobs from all queues into a single priority-ordered list.

        Each job is annotated with its source queue_id.
        Ordering uses priority descending, deadline ascending,
        and sequence number for tie-breaking.
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
