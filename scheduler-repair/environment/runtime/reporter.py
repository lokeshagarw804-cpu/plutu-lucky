"""
Reporter module — computes scheduling statistics and worker utilization.
"""

from configparser import ConfigParser


def load_config():
    config = ConfigParser()
    config.read("/app/runtime/config.ini")
    return config


def compute_stats(schedule):
    """Compute overall scheduling statistics."""
    total_jobs = len(schedule)
    on_time_count = sum(1 for entry in schedule if entry["on_time"])
    violation_count = total_jobs - on_time_count
    return {
        "total_jobs": total_jobs,
        "on_time_count": on_time_count,
        "violation_count": violation_count,
    }


def compute_worker_utilization(schedule):
    """Compute per-worker utilization as fraction of max_deadline window used."""
    config = load_config()
    max_deadline = config.getint("timing", "max_deadline_ms")

    worker_times = {}
    for entry in schedule:
        worker = entry["worker"]
        job_time = entry["finish_ms"] - entry["start_ms"]
        if worker not in worker_times:
            worker_times[worker] = 0
        total_time = job_time
        worker_times[worker] = total_time

    utilization = {}
    for worker, total in worker_times.items():
        utilization[worker] = round(total / max_deadline, 4)

    return utilization


def generate_report(schedule):
    """Generate the full scheduling report."""
    stats = compute_stats(schedule)
    utilization = compute_worker_utilization(schedule)
    stats["worker_utilization"] = utilization
    return stats
