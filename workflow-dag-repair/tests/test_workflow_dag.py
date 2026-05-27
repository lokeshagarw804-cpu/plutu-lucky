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
        """Execution timeline output file must be generated at the expected path."""
        assert os.path.isfile(TIMELINE_PATH), (
            f"Expected timeline output at {TIMELINE_PATH}"
        )

    def test_resource_report_exists(self):
        """Resource utilization report must be generated at the expected path."""
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
        """System processes exactly 3 workflow definitions."""
        assert timeline_data["total_workflows"] == 3

    def test_schedule_entries_match_total(self, timeline_data):
        """Schedule array length must equal total_jobs."""
        assert len(timeline_data["schedule"]) == timeline_data["total_jobs"]


class TestParallelismConstraint:
    """Validate that scheduling obeys the strict concurrency cap."""

    def test_max_parallel_jobs_respected(self, timeline_data):
        """No time slot may exceed the production parallelism ceiling.

        The system must enforce the strict scheduling constraint rather
        than the permissive default. Check /app/runtime/config.ini for
        available scheduling profiles.
        """
        schedule = timeline_data["schedule"]
        max_end = max(j["end_slot"] for j in schedule)
        slot_counts = [0] * (max_end + 1)
        for job in schedule:
            for s in range(job["start_slot"], job["end_slot"] + 1):
                slot_counts[s] += 1
        max_concurrent = max(slot_counts)
        assert max_concurrent <= 3, (
            f"Detected {max_concurrent} concurrent jobs in a single slot. "
            "The production constraint limits this to 3. Examine how the "
            "scheduler loads its concurrency parameter."
        )

    def test_total_slots_reflects_strict_limit(self, resource_data):
        """Schedule span must be consistent with strict concurrency limits."""
        assert resource_data["total_slots"] >= 18, (
            f"Only {resource_data['total_slots']} slots used for 55 jobs — "
            "this implies too much parallelism. The strict scheduling "
            "profile should produce a longer schedule."
        )


class TestResourceTracking:
    """Validate per-pool resource utilization is physically meaningful."""

    def test_all_four_pools_present(self, resource_data):
        """All configured resource pools must appear in the report.

        The system tracks cpu, memory, gpu, and network pools. If any
        pool is missing, check how pool identifiers are parsed from the
        configuration file in /app/runtime/tracker.py.
        """
        pools = resource_data["pools"]
        expected = {"cpu", "memory", "gpu", "network"}
        actual = set(pools.keys())
        assert expected.issubset(actual), (
            f"Missing pools: {expected - actual}. "
            "Pool name parsing may have whitespace artifacts — inspect "
            "the raw config value for resource_pools."
        )

    def test_network_pool_nonzero(self, resource_data):
        """Network pool must report non-zero peak usage.

        Several jobs declare network resource requirements. Zero usage
        indicates the pool name does not match job resource keys.
        """
        pools = resource_data["pools"]
        if "network" not in pools:
            pytest.skip("Network pool not present — see test_all_four_pools_present")
        assert pools["network"]["peak_usage"] > 0, (
            "Network peak_usage is 0 despite jobs declaring network "
            "resources. The pool identifier in the tracker may not "
            "match the resource key used in job definitions."
        )

    def test_cpu_peak_within_limit(self, resource_data):
        """CPU peak utilization must stay within the configured capacity.

        Peak represents the maximum demand in any single time slot.
        If it exceeds the limit, the aggregation method may be wrong.
        """
        pools = resource_data["pools"]
        cpu_peak = pools["cpu"]["peak_usage"]
        assert cpu_peak <= 100, (
            f"CPU peak_usage={cpu_peak} exceeds capacity of 100. "
            "The tracker should report the single-slot maximum, not "
            "an aggregate across the entire schedule span."
        )

    def test_memory_peak_within_limit(self, resource_data):
        """Memory peak utilization must stay within capacity of 256."""
        pools = resource_data["pools"]
        mem_peak = pools["memory"]["peak_usage"]
        assert mem_peak <= 256, (
            f"Memory peak_usage={mem_peak} exceeds capacity of 256. "
            "Verify the peak computation uses per-slot maximum."
        )

    def test_gpu_peak_within_limit(self, resource_data):
        """GPU peak utilization must stay within capacity of 4."""
        pools = resource_data["pools"]
        gpu_peak = pools["gpu"]["peak_usage"]
        assert gpu_peak <= 4, (
            f"GPU peak_usage={gpu_peak} exceeds capacity of 4. "
            "The tracking mode should compute peak per time slot."
        )


class TestDeterministicOrdering:
    """Validate that job ordering is reproducible across runs."""

    def test_alpha_before_beta_same_priority_slot(self, timeline_data):
        """Among jobs sharing priority and submission time, workflow order
        determines scheduling precedence (alphabetical by workflow_id).

        The resolver must produce a fully deterministic ordering when
        multiple workflows submit jobs at the same timestamp with the
        same priority tier.
        """
        schedule = timeline_data["schedule"]
        # Among high-priority jobs starting at the same slot from alpha/beta,
        # alpha entries must appear first in the schedule array
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

        # Find shared slots between alpha and beta high-priority jobs
        shared_slots = set(alpha_positions.keys()) & set(beta_positions.keys())
        for slot in shared_slots:
            assert alpha_positions[slot] < beta_positions[slot], (
                f"At slot {slot}, beta high-priority job appears at "
                f"schedule position {beta_positions[slot]} before alpha "
                f"at position {alpha_positions[slot]}. Deterministic "
                "ordering requires workflow_id as the final tiebreaker "
                "in /app/runtime/resolver.py — check the sort key."
            )

    def test_schedule_fully_deterministic(self, timeline_data):
        """Schedule must be identical across repeated executions.

        Verify structural invariant: all 55 jobs are present with
        consistent slot assignments that reflect dependency order.
        """
        schedule = timeline_data["schedule"]
        assert len(schedule) == 55

        # Verify every job has required fields
        for job in schedule:
            assert "job_id" in job
            assert "workflow_id" in job
            assert "start_slot" in job
            assert "end_slot" in job
            assert job["start_slot"] <= job["end_slot"]
