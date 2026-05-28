"""Rebase reporter -- generates structured JSON output files.

Produces the rebase plan and conflict report as JSON documents
containing linearized commit sequences, conflict annotations,
and dependency group metadata for downstream tooling.
"""
import json
import os


class RebaseReporter:
    """Generates rebase analysis output reports."""

    def __init__(self, output_dir):
        self._output_dir = output_dir

    def write_reports(self, linearized, conflicts, scored_groups, all_commits):
        """Write rebase analysis output files.

        Produces:
          - rebase_plan.json: Linearized commit sequence with ordering metadata
          - conflict_report.json: Detected conflicts and group scoring
        """
        os.makedirs(self._output_dir, exist_ok=True)

        # Write rebase plan
        plan = {
            "total_commits": len(linearized),
            "total_groups": len(scored_groups),
            "commits": [
                {
                    "commit_id": c["commit_id"],
                    "branch": c["source_branch"],
                    "message": c["message"],
                    "timestamp": c["timestamp"],
                    "patch_type": c["patch_type"],
                    "files_modified": c["files_modified"],
                }
                for c in linearized
            ],
            "groups": scored_groups,
        }
        plan_path = os.path.join(self._output_dir, "rebase_plan.json")
        with open(plan_path, "w") as f:
            json.dump(plan, f, indent=2)

        # Write conflict report
        report = {
            "total_conflicts": len(conflicts),
            "total_commits_analyzed": len(all_commits),
            "conflicts": conflicts,
        }
        report_path = os.path.join(self._output_dir, "conflict_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
