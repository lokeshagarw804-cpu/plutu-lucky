"""Feed loader — reads POI records from JSONL source feeds.

Loads all .jsonl files from the configured source directory,
parses records, and filters by allowed categories from config.
"""
import configparser
import json
import os


class FeedLoader:
    """Loads and filters POI records from multiple feed files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        source_dir = self._config.get("feeds", "source_dir")
        self._source_dir = source_dir
        raw_categories = self._config.get("feeds", "allowed_categories")
        self._allowed = set(raw_categories.split(","))

    def load_all_feeds(self):
        """Load records from all feed files, filtered by allowed categories."""
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
                    if record.get("category") in self._allowed:
                        all_records.append(record)
        return all_records
