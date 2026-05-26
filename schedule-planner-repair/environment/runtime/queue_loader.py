"""Queue loader — reads job definitions from configured queue source files.

Each queue file contains a set of jobs submitted to a particular
scheduling queue (batch, interactive, realtime, maintenance). Jobs are
loaded and tagged with their originating queue identifier.
"""
import configparser
import json
import os


class QueueLoader:
    """Loads job definitions from configured queue source files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("queues", "source_dir")
        raw_queues = self._config.get("queues", "active_queues")
        self._active = set(raw_queues.split(","))

    def load_queues(self):
        """Load all jobs from active queue files.

        Returns dict mapping queue_id to list of job dicts.
        Only queues listed in the active_queues config are loaded.
        """
        queues = {}
        for filename in os.listdir(self._source_dir):
            if not filename.endswith(".json"):
                continue
            queue_id = filename.replace(".json", "")
            if queue_id not in self._active:
                continue
            filepath = os.path.join(self._source_dir, filename)
            with open(filepath, "r") as f:
                data = json.load(f)
            queues[queue_id] = data["jobs"]
        return queues
