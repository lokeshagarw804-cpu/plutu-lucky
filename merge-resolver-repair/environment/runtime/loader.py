"""Branch history loader — reads divergent edit histories from JSON files.

Loads base, left, and right branch data for three-way merge computation.
Each branch file contains line-level edits with metadata about the
modification context.
"""
import configparser
import json
import os


class BranchLoader:
    """Loads branch history data from JSON files for merge resolution."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("merge", "source_dir")

    def load_branches(self):
        """Load all branch history files from the data directory.

        Returns dict mapping branch_id to branch data with edits and metadata.
        """
        branches = {}
        for fname in sorted(os.listdir(self._source_dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._source_dir, fname)
            with open(path, "r") as f:
                data = json.load(f)
            branch_id = data["branch_id"]
            branches[branch_id] = {
                "branch_id": branch_id,
                "parent_commit": data["parent_commit"],
                "edits": data["edits"],
                "timestamp": data["timestamp"],
            }
        return branches
