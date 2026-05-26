"""
Queue-based task filter.

Removes tasks from queues not in the active priority queue list.
Only tasks belonging to configured priority queues proceed to
the scheduling engine for priority computation.
"""

import configparser


class QueueFilter:
    """Filters tasks by active queue membership."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        raw_queues = config.get("queues", "priority_queues")
        self._active_queues = set(raw_queues.split(","))

    def filter_tasks(self, tasks):
        """Return only tasks whose queue_id is in the active set."""
        return [t for t in tasks if t["queue_id"] in self._active_queues]
