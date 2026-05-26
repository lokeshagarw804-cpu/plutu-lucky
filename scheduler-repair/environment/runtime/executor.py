"""
Executor module — simulates job execution on workers and checks deadlines.
"""


def simulate_execution(assignments):
    """
    Simulate execution across workers. Each worker processes jobs sequentially
    in the order they were assigned. Returns the execution schedule.
    """
    worker_clocks = {}
    schedule = []

    for task in assignments:
        worker = task["worker"]
        duration = task["duration_ms"]
        deadline = task["deadline_ms"]

        if worker not in worker_clocks:
            worker_clocks[worker] = 0

        start_ms = worker_clocks[worker]
        finish_ms = start_ms + duration

        on_time = finish_ms < deadline

        schedule.append({
            "job_id": task["job_id"],
            "worker": worker,
            "start_ms": start_ms,
            "finish_ms": finish_ms,
            "on_time": on_time,
        })

        worker_clocks[worker] = finish_ms

    return schedule
