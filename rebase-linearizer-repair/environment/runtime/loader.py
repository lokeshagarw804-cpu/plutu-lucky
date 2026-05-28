"""Branch commit loader -- reads commit histories from JSON data files.

Loads feature branch data from the configured source directory. Each
branch file contains a sequence of commit records with metadata about
modifications, dependencies, and patch classification.
"""
import configparser
import json
import os


class BranchLoader:
    """Loads branch commit histories from JSON files for rebase linearization."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("rebase", "source_dir")

    def load_branches(self):
        """Load all branch history files from the data directory.

        Returns list of all commits across all branches, sorted by timestamp.
        Each commit carries its branch identifier and patch metadata.
        """
        all_commits = []
        for fname in sorted(os.listdir(self._source_dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._source_dir, fname)
            with open(path, "r") as f:
                data = json.load(f)
            branch_name = data["branch"]
            for commit in data["commits"]:
                commit["source_branch"] = branch_name
                all_commits.append(commit)

        all_commits.sort(key=lambda c: c["timestamp"])
        return all_commits
