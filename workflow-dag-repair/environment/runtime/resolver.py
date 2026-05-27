"""Dependency resolver — computes execution order using topological sort.

Resolves DAG dependencies within each workflow and across all jobs,
producing a global execution order that respects dependencies and
priorities. Jobs are ordered by priority tier first, then by submission
timestamp for deterministic scheduling.
"""


PRIORITY_MAP = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


class DependencyResolver:
    """Resolves job dependencies and produces execution ordering."""

    def resolve(self, workflows):
        """Compute global execution order from all workflow DAGs.

        Produces a topological ordering where:
        - Dependencies are always scheduled before dependents
        - Among ready jobs, ordering is by (priority, submit_time)

        Note: submit_time is shared across workflow batches
        """
        all_jobs = {}
        for wf_id, wf_data in workflows.items():
            for job in wf_data["jobs"]:
                all_jobs[job["job_id"]] = {
                    **job,
                    "workflow_id": wf_id,
                    "submit_time": wf_data["submit_time"],
                }

        # Build adjacency and in-degree
        in_degree = {jid: 0 for jid in all_jobs}
        dependents = {jid: [] for jid in all_jobs}

        for jid, job in all_jobs.items():
            for dep in job["depends_on"]:
                if dep in all_jobs:
                    in_degree[jid] += 1
                    dependents[dep].append(jid)

        # Kahn's algorithm with priority queue simulation
        ready = [jid for jid, deg in in_degree.items() if deg == 0]
        ready.sort(key=lambda jid: (
            PRIORITY_MAP.get(all_jobs[jid]["priority"], 99),
            all_jobs[jid]["submit_time"],
        ))

        ordered = []
        while ready:
            current = ready.pop(0)
            ordered.append(all_jobs[current])

            for dep_id in dependents[current]:
                in_degree[dep_id] -= 1
                if in_degree[dep_id] == 0:
                    ready.append(dep_id)

            ready.sort(key=lambda jid: (
                PRIORITY_MAP.get(all_jobs[jid]["priority"], 99),
                all_jobs[jid]["submit_time"],
            ))

        return ordered
