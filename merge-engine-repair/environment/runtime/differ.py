"""Diff engine — computes file-level differences between branches.

Processes commit histories to determine which files were modified
on each branch relative to their merge base. Groups changes into
fixed-size chunks for conflict detection.

Chunking splits the file list into groups of chunk_size for parallel
conflict analysis. The number of chunks should be computed as:
ceil(file_count / chunk_size).
"""
import configparser
import math


class DiffEngine:
    """Computes file diffs between branch and its merge base."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._chunk_size = self._config.getint("merge", "chunk_size")

    def compute_diffs(self, branches):
        """Compute per-branch file modifications from commit histories.

        For each branch, collects all files touched by any commit and
        determines the latest version. Returns dict of branch_id to
        file change sets.
        """
        branch_diffs = {}

        for branch_id, branch_data in branches.items():
            file_versions = {}
            for commit in branch_data["commits"]:
                for filename, version in commit["files"].items():
                    file_versions[filename] = {
                        "version": version,
                        "commit": commit["hash"],
                        "timestamp": commit["timestamp"],
                    }
            branch_diffs[branch_id] = file_versions

        return branch_diffs

    def chunk_files(self, file_set):
        """Split file set into fixed-size chunks for processing.

        Returns list of file chunks. Number of chunks is
        ceil(file_count / chunk_size).
        """
        files = sorted(file_set)
        chunks = []
        # Off by one: uses chunk_size + 1 as step
        for i in range(0, len(files), self._chunk_size + 1):
            chunk = files[i:i + self._chunk_size + 1]
            chunks.append(chunk)
        return chunks

    def get_chunk_count(self, file_count):
        """Compute expected number of chunks for a file count."""
        return math.ceil(file_count / (self._chunk_size + 1))
