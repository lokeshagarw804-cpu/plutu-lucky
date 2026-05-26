"""
Dispatcher module — loads job queues, sorts by priority, and assigns to workers.
"""

import json
import os
from configparser import ConfigParser


def load_config():
    config = ConfigParser()
    config.read("/app/runtime/config.ini")
    return config


def load_jobs(queue_dir):
    """Load all jobs from JSONL queue files."""
    jobs = []
    for fname in sorted(os.listdir(queue_dir)):
        if fname.endswith(".jsonl"):
            fpath = os.path.join(queue_dir, fname)
            with open(fpath, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        jobs.append(json.loads(line))
    return jobs


def sort_jobs(jobs):
    """Sort jobs for optimal scheduling: highest priority first, then earliest deadline."""
    sorted_jobs = sorted(jobs, key=lambda j: (-j["priority"], j["deadline_ms"]))
    return sorted_jobs


def assign_workers(sorted_jobs, worker_names):
    """Assign each job to its preferred worker based on affinity."""
    assignments = []
    for job in sorted_jobs:
        worker = job["worker_affinity"]
        if worker not in worker_names:
            worker = worker_names[0]
        assignments.append({
            "job_id": job["job_id"],
            "priority": job["priority"],
            "deadline_ms": job["deadline_ms"],
            "duration_ms": job["duration_ms"],
            "worker": worker,
        })
    return assignments


def dispatch():
    """Main dispatch routine: load, sort, assign."""
    config = load_config()
    queue_dir = config.get("scheduler", "queue_dir")
    worker_names = [w.strip() for w in config.get("workers", "names").split(",")]

    jobs = load_jobs(queue_dir)
    sorted_jobs = sort_jobs(jobs)
    assignments = assign_workers(sorted_jobs, worker_names)
    return assignments
