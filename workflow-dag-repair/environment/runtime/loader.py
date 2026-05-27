"""Workflow loader — reads job definitions from JSON workflow files."""
import configparser
import json
import os


class WorkflowLoader:
    """Loads workflow definitions from the configured source directory."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("workflows", "source_dir")

    def load_workflows(self):
        """Load all workflow files from the source directory.

        Returns a dict mapping workflow_id to its parsed definition.
        """
        workflows = {}
        for fname in sorted(os.listdir(self._source_dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._source_dir, fname)
            with open(path, "r") as f:
                data = json.load(f)
            wf_id = data["workflow_id"]
            workflows[wf_id] = {
                "workflow_id": wf_id,
                "submit_time": data["submit_time"],
                "jobs": data["jobs"],
            }
        return workflows
