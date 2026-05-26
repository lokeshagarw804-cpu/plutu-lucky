"""Feed loader — reads POI records from JSONL source feeds.

Loads all .jsonl files from the configured source directory and
returns raw record dicts. Filtering is handled downstream by the
normalizer stage which applies category constraints.
"""
import configparser
import json
import os


class FeedLoader:
    """Loads raw POI records from multiple feed files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("feeds", "source_dir")

    def load_all_feeds(self):
        """Load all records from feed files without filtering."""
        all_records = []
        feed_files = sorted(
            f for f in os.listdir(self._source_dir) if f.endswith(".jsonl")
        )
        for fname in feed_files:
            path = os.path.join(self._source_dir, fname)
            with open(path, "r") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    all_records.append(record)
        return all_records
