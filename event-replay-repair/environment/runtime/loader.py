"""
Event stream loader.

Reads event records from stream JSON files in /app/runtime/data/.
Each stream file represents a distinct event source (orders, payments,
inventory) with its own sequence numbering.
"""

import json
import os


def load_events(data_dir="/app/runtime/data"):
    """Load all events from stream data files.

    Returns a list of event dicts from all stream sources.
    """
    events = []
    for filename in sorted(os.listdir(data_dir)):
        if filename.endswith("_stream.json"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r") as f:
                records = json.load(f)
                events.extend(records)
    return events
