"""Report generator — produces execution timeline and resource reports.

Assembles the final output JSON files from scheduled jobs and resource
utilization data. Workflow completion is measured as the slot index
following the last job's end slot.
"""
import json
import os


class ReportGenerator:
    """Generates output reports from scheduling results."""

    def __init__(self, output_dir):
        self._output_dir = output_dir

    def generate(self, scheduled_jobs, utilization):
        """Write execution timeline and resource report to output directory."""
        os.makedirs(self._output_dir, exist_ok=True)

        timeline = self._build_timeline(scheduled_jobs)
        with open(os.path.join(self._output_dir, "execution_timeline.json"), "w") as f:
            json.dump(timeline, f, indent=2)

        resource_report = self._build_resource_report(utilization)
        with open(os.path.join(self._output_dir, "resource_report.json"), "w") as f:
            json.dump(resource_report, f, indent=2)

    def _build_timeline(self, scheduled_jobs):
        """Build execution timeline with per-workflow summaries."""
        workflows = {}
        for job in scheduled_jobs:
            wf = job["workflow_id"]
            if wf not in workflows:
                workflows[wf] = {"jobs": [], "makespan": 0}
            workflows[wf]["jobs"].append(job)
            # Track latest completion: end_slot is inclusive, so completion
            # is end_slot + 1 (the next available slot after this job finishes)
            completion = job["end_slot"]
            if completion > workflows[wf]["makespan"]:
                workflows[wf]["makespan"] = completion

        # Sort workflows alphabetically for deterministic output
        workflow_summaries = []
        for wf_id in sorted(workflows.keys()):
            wf_data = workflows[wf_id]
            workflow_summaries.append({
                "workflow_id": wf_id,
                "job_count": len(wf_data["jobs"]),
                "makespan": wf_data["makespan"],
            })

        return {
            "total_jobs": len(scheduled_jobs),
            "total_workflows": len(workflows),
            "workflows": workflow_summaries,
            "schedule": scheduled_jobs,
        }

    def _build_resource_report(self, utilization):
        """Build resource utilization report."""
        return {
            "total_slots": utilization["total_slots"],
            "pools": utilization["pools"],
            "slot_count": len(utilization["slot_breakdown"]),
            "slot_breakdown": utilization["slot_breakdown"],
        }
