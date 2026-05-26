"""Branch loader — reads branch history files from data directory.

Loads JSON-format branch files containing commit histories. Only
branches whose merge strategy appears in the active_strategies
configuration are loaded for processing.
"""
import configparser
import json
import os


class BranchLoader:
    """Loads branch histories from data directory based on active strategies."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("branches", "source_dir")
        raw_strategies = self._config.get("branches", "active_strategies")
        self._active_strategies = set(raw_strategies.split(","))

    def load_branches(self):
        """Load all branch files and filter to active strategies.

        Returns dict mapping branch_id to branch data (with commits list).
        Only branches whose strategy appears in active_strategies are loaded.
        """
        branches = {}
        for fname in sorted(os.listdir(self._source_dir)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(self._source_dir, fname)
            with open(fpath, "r") as f:
                data = json.load(f)

            strategy = data.get("strategy", "")
            if strategy in self._active_strategies:
                branches[data["branch_id"]] = data

        return branches
