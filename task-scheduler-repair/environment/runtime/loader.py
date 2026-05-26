"""Job queue loader — reads job definitions from queue data files.

Loads JSON-format queue files from the configured source directory.
Each queue file represents a distinct worker pool with its own set
of pending jobs. Only jobs from active worker types are loaded.
"""
import configparser
import json
import os


class QueueLoader:
    """Loads job queues from data directory based on active worker config."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("queues", "source_dir")
        raw_workers = self._config.get("queues", "active_workers")
        self._active_workers = set(raw_workers.split(","))

    def load_queues(self):
        """Load all queue files and filter to active worker types.

        Returns dict mapping queue_id to queue data (with jobs list).
        Only queues whose worker_type appears in active_workers are included.
        """
        queues = {}
        for fname in os.listdir(self._source_dir):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(self._source_dir, fname)
            with open(fpath, "r") as f:
                data = json.load(f)

            worker_type = data.get("worker_type", "")
            if worker_type in self._active_workers:
                queues[data["queue_id"]] = data

        return queues
