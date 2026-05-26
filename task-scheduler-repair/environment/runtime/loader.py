"""
Task queue loader.

Reads task definitions from queue JSON files in /app/runtime/data/.
Each queue file represents a distinct priority tier with its own
set of scheduled tasks.
"""

import json
import os


def load_queues(data_dir="/app/runtime/data"):
    """Load all task records from queue data files.

    Returns a list of task dicts from all queue sources.
    """
    tasks = []
    for filename in sorted(os.listdir(data_dir)):
        if filename.startswith("queue_") and filename.endswith(".json"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r") as f:
                records = json.load(f)
                tasks.extend(records)
    return tasks
