"""Merge reporter — generates structured merge analysis output.

Produces JSON reports containing merge statistics, conflict details,
and region-level scoring information for downstream tooling consumption.
"""
import json
import os


class MergeReporter:
    """Generates merge analysis reports."""

    def __init__(self, output_dir):
        self._output_dir = output_dir

    def write_reports(self, resolution, scored_regions, branches):
        """Write merge analysis output files.

        Produces:
          - merge_report.json: Full conflict details and resolution metadata
          - region_summary.json: Scored region overview
        """
        os.makedirs(self._output_dir, exist_ok=True)

        # Write main merge report
        report = {
            "total_conflicts": resolution["total_conflicts"],
            "total_auto_resolved": resolution["total_auto_resolved"],
            "strategies_used": resolution["strategies_used"],
            "branch_count": len(branches),
            "conflicts": resolution["conflicts"],
        }
        report_path = os.path.join(self._output_dir, "merge_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Write region summary
        summary = {
            "total_regions": len(scored_regions),
            "conflicting_regions": sum(
                1 for r in scored_regions if r["has_conflict"]
            ),
            "clean_regions": sum(
                1 for r in scored_regions if not r["has_conflict"]
            ),
            "regions": scored_regions,
        }
        summary_path = os.path.join(self._output_dir, "region_summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
