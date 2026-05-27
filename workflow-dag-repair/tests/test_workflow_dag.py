"""Validation tests for workflow DAG execution engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
TIMELINE_PATH = os.path.join(OUTPUT_DIR, "execution_timeline.json")
RESOURCE_PATH = os.path.join(OUTPUT_DIR, "resource_report.json")


@pytest.fixture(scope="module")
def timeline_data():
    """Load execution timeline output."""
    with open(TIMELINE_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def resource_data():
    """Load resource utilization report."""
    with open(RESOURCE_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file structure validation."""

    def test_timeline_file_exists(self):
        """Execution timeline output file must be generated."""
        assert os.path.isfile(TIMELINE_PATH), (
            f"Expected timeline output at {TIMELINE_PATH}"
        )

    def test_resource_report_exists(self):
        """Resource utilization report must be generated."""
        assert os.path.isfile(RESOURCE_PATH), (
            f"Expected resource report at {RESOURCE_PATH}"
        )

    def test_timeline_has_required_fields(self, timeline_data):
        """Timeline must contain total_jobs, total_workflows, workflows, schedule."""
        assert "total_jobs" in timeline_data
        assert "total_workflows" in timeline_data
        assert "workflows" in timeline_data
        assert "schedule" in timeline_data

    def test_resource_report_has_required_fields(self, resource_data):
        """Resource report must contain total_slots, pools, slot_count, slot_breakdown."""
        assert "total_slots" in resource_data
        assert "pools" in resource_data
        assert "slot_count" in resource_data
        assert "slot_breakdown" in resource_data


class TestJobCounts:
    """Validate total job counts and workflow membership."""

    def test_total_job_count(self, timeline_data):
        """All 55 jobs from 3 workflows must appear in the schedule."""
        assert timeline_data["total_jobs"] == 55

    def test_workflow_count(self, timeline_data):
        """System must process exactly 3 workflow definitions."""
        assert timeline_data["total_workflows"] == 3

    def test_schedule_entries_match_total(self, timeline_data):
        """Schedule array length must equal total_jobs."""
        assert len(timeline_data["schedule"]) == timeline_data["total_jobs"]


class TestConcurrencyLimits:
    """Validate that scheduling obeys production concurrency bounds."""

    def test_max_concurrent_jobs(self, timeline_data):
        """No time slot may have more than 3 concurrent jobs.

        The system must enforce the production deployment limit rather
        than permissive defaults.
        """
        schedule = timeline_data["schedule"]
        max_end = max(j["end_slot"] for j in schedule)
        slot_counts = [0] * (max_end + 1)
        for job in schedule:
            for s in range(job["start_slot"], job["end_slot"] + 1):
                slot_counts[s] += 1
        max_concurrent = max(slot_counts)
        assert max_concurrent <= 3, (
            f"Detected {max_concurrent} concurrent jobs in a single slot "
            f"but production limit is 3."
        )

    def test_schedule_span_minimum(self, resource_data):
        """With max 3 parallel jobs, 55 jobs require at least 18 slots."""
        assert resource_data["total_slots"] >= 18, (
            f"Schedule uses only {resource_data['total_slots']} slots for "
            f"55 jobs — concurrency is not properly constrained."
        )


class TestResourcePools:
    """Validate resource pool tracking correctness."""

    def test_all_four_pools_present(self, resource_data):
        """All four configured pools (cpu, memory, gpu, network) must appear."""
        pools = resource_data["pools"]
        expected = {"cpu", "memory", "gpu", "network"}
        actual = set(pools.keys())
        missing = expected - actual
        assert not missing, (
            f"Pools {missing} are missing from the resource report."
        )

    def test_network_pool_nonzero(self, resource_data):
        """Network pool must show non-zero usage since jobs declare it."""
        pools = resource_data["pools"]
        if "network" not in pools:
            pytest.skip("Network pool not present")
        assert pools["network"]["peak_usage"] > 0, (
            "Network peak_usage is 0 but multiple jobs require network resources."
        )

    def test_cpu_within_capacity(self, resource_data):
        """CPU peak must not exceed the pool capacity of 100."""
        pools = resource_data["pools"]
        assert pools["cpu"]["peak_usage"] <= 100, (
            f"CPU peak_usage={pools['cpu']['peak_usage']} exceeds capacity."
        )

    def test_memory_within_capacity(self, resource_data):
        """Memory peak must not exceed the pool capacity of 256."""
        pools = resource_data["pools"]
        assert pools["memory"]["peak_usage"] <= 256, (
            f"Memory peak_usage={pools['memory']['peak_usage']} exceeds capacity."
        )

    def test_gpu_within_capacity(self, resource_data):
        """GPU peak must not exceed the pool capacity of 4."""
        pools = resource_data["pools"]
        assert pools["gpu"]["peak_usage"] <= 4, (
            f"GPU peak_usage={pools['gpu']['peak_usage']} exceeds capacity."
        )


class TestWorkflowMakespan:
    """Validate per-workflow completion time reporting."""

    def test_makespan_equals_end_slot_plus_one(self, timeline_data):
        """Each workflow's makespan must equal max(end_slot) + 1.

        Since end_slot is inclusive, the number of slots from start to
        completion is one more than the latest end_slot index.
        """
        schedule = timeline_data["schedule"]
        workflows = timeline_data["workflows"]

        # Compute expected makespan from schedule data
        wf_max_end = {}
        for job in schedule:
            wf = job["workflow_id"]
            if wf not in wf_max_end or job["end_slot"] > wf_max_end[wf]:
                wf_max_end[wf] = job["end_slot"]

        for wf_summary in workflows:
            wf_id = wf_summary["workflow_id"]
            expected = wf_max_end[wf_id] + 1
            actual = wf_summary["makespan"]
            assert actual == expected, (
                f"Workflow '{wf_id}' makespan is {actual} but expected "
                f"{expected} (max end_slot {wf_max_end[wf_id]} + 1)."
            )


class TestDeterministicOrdering:
    """Validate fully deterministic scheduling across repeated runs."""

    def test_alpha_before_beta_at_shared_slots(self, timeline_data):
        """When alpha and beta high-priority jobs share a time slot,
        alpha must appear first in the schedule (alphabetical tiebreaker).
        """
        schedule = timeline_data["schedule"]
        alpha_positions = {}
        beta_positions = {}
        for i, job in enumerate(schedule):
            if job["priority"] == "high" and job["workflow_id"] == "alpha":
                slot = job["start_slot"]
                if slot not in alpha_positions:
                    alpha_positions[slot] = i
            elif job["priority"] == "high" and job["workflow_id"] == "beta":
                slot = job["start_slot"]
                if slot not in beta_positions:
                    beta_positions[slot] = i

        shared = set(alpha_positions.keys()) & set(beta_positions.keys())
        for slot in shared:
            assert alpha_positions[slot] < beta_positions[slot], (
                f"At slot {slot}, beta appears before alpha in schedule "
                f"(positions {beta_positions[slot]} vs {alpha_positions[slot]})."
            )

    def test_schedule_structural_integrity(self, timeline_data):
        """All 55 jobs must have valid slot assignments."""
        schedule = timeline_data["schedule"]
        assert len(schedule) == 55
        for job in schedule:
            assert "job_id" in job
            assert "workflow_id" in job
            assert "start_slot" in job
            assert "end_slot" in job
            assert job["start_slot"] <= job["end_slot"]
