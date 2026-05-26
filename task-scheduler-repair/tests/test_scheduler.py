"""Validation tests for task scheduler engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
MANIFEST_PATH = os.path.join(OUTPUT_DIR, "execution_manifest.json")
REPORT_PATH = os.path.join(OUTPUT_DIR, "utilization_report.json")


@pytest.fixture(scope="module")
def manifest_data():
    """Load execution manifest output."""
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def report_data():
    """Load utilization report output."""
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file validation — ensures system runs to completion."""

    def test_manifest_file_exists(self):
        """Execution manifest output must be generated."""
        assert os.path.isfile(MANIFEST_PATH), (
            "execution_manifest.json not found at /app/runtime/output/"
        )

    def test_report_file_exists(self):
        """Utilization report output must be generated."""
        assert os.path.isfile(REPORT_PATH), (
            "utilization_report.json not found at /app/runtime/output/"
        )

    def test_manifest_structure(self, manifest_data):
        """Manifest output has required top-level fields."""
        assert "total_jobs" in manifest_data
        assert "total_batches" in manifest_data
        assert "batches" in manifest_data
        assert "scheduling_order" in manifest_data
        assert "timing" in manifest_data

    def test_report_structure(self, report_data):
        """Report output has required top-level fields."""
        assert "total_resource_units" in report_data
        assert "per_type_totals" in report_data
        assert "batch_count" in report_data
        assert "batch_snapshots" in report_data
        assert "active_worker_types" in report_data


class TestJobLoading:
    """Validates that all configured worker queues are loaded correctly."""

    def test_total_job_count(self, manifest_data):
        """All 53 jobs from active worker queues must be scheduled.

        Three queues are active: compute (18), io (15), gpu (20).
        Check /app/runtime/config.ini active_workers list and ensure
        all worker types are being matched correctly during loading.
        """
        assert manifest_data["total_jobs"] == 53, (
            f"Expected 53 total jobs from 3 active queues, got "
            f"{manifest_data['total_jobs']}. Check worker type matching "
            f"in /app/runtime/loader.py against config active_workers list."
        )

    def test_gpu_jobs_present(self, manifest_data):
        """GPU worker queue jobs must appear in scheduling order."""
        order = manifest_data["scheduling_order"]
        gpu_jobs = [j for j in order if j.startswith("g")]
        assert len(gpu_jobs) == 20, (
            f"Expected 20 gpu jobs in scheduling order, found {len(gpu_jobs)}. "
            f"Check that the gpu worker type matches active_workers config."
        )

    def test_active_worker_types(self, report_data):
        """Report must list all 3 active worker types."""
        types = report_data["active_worker_types"]
        assert "gpu" in types, (
            "gpu missing from active_worker_types. Check worker type "
            "parsing in /app/runtime/loader.py."
        )
        assert "compute" in types
        assert "io" in types


class TestBatchScheduling:
    """Validates batch assignment with correct capacity constraints."""

    def test_batch_count(self, manifest_data):
        """Must produce exactly 12 batches with correct capacity.

        The batch capacity from scheduling.precise section is 12
        resource units per batch. Check which config section the
        batch scheduler reads from in /app/runtime/batch_scheduler.py.
        """
        assert manifest_data["total_batches"] == 12, (
            f"Expected 12 batches with capacity=12, got "
            f"{manifest_data['total_batches']} batches. Check config "
            f"section used for batch_capacity in /app/runtime/batch_scheduler.py "
            f"— the precise scheduling parameters are in [scheduling.precise]."
        )

    def test_batch_capacity_respected(self, manifest_data):
        """No batch should exceed the configured capacity of 12."""
        for batch in manifest_data["batches"]:
            assert batch["total_resource_units"] <= 12, (
                f"Batch {batch['batch_id']} has {batch['total_resource_units']} "
                f"resource units, exceeding capacity 12."
            )

    def test_batch_utilization_range(self, manifest_data):
        """Each batch utilization must be between 0 and 1."""
        for batch in manifest_data["batches"]:
            assert 0 < batch["utilization"] <= 1.0


class TestPriorityOrdering:
    """Validates deterministic priority-based scheduling order."""

    def test_highest_priority_first(self, manifest_data):
        """The first scheduled job must be i015 (highest score)."""
        assert manifest_data["scheduling_order"][0] == "i015"

    def test_tiebreaker_ordering(self, manifest_data):
        """Jobs c016 and g011 have identical scores and timestamps.

        When priority_score and submitted_at are equal, the scheduler
        must break ties using queue_id alphabetically, then seq within
        that queue. This means c016 (compute) must come before g011 (gpu).
        Check sort key in /app/runtime/priority_scorer.py — seq alone
        is not sufficient since seq is local to each queue.
        """
        order = manifest_data["scheduling_order"]
        assert "g011" in order, (
            "g011 not found in scheduling order — gpu queue jobs are "
            "missing. Check worker type loading in /app/runtime/loader.py."
        )
        assert "c016" in order, (
            "c016 not found in scheduling order."
        )
        pos_c016 = order.index("c016")
        pos_g011 = order.index("g011")
        assert pos_c016 < pos_g011, (
            f"c016 at position {pos_c016} must come before g011 at "
            f"position {pos_g011}. These jobs have identical priority "
            f"scores and timestamps — tie must be broken by queue_id "
            f"then seq. Check sort key in /app/runtime/priority_scorer.py."
        )

    def test_descending_priority(self, manifest_data):
        """Scheduling order must follow descending priority scores."""
        order = manifest_data["scheduling_order"]
        # First 5 jobs should all start with 'i' or 'c' (highest urgency io jobs)
        assert order[0] == "i015"
        assert order[1] == "i013"
        assert order[2] == "i011"


class TestResourceUtilization:
    """Validates resource tracking computes per-batch snapshots correctly."""

    def test_total_resource_units(self, report_data):
        """Total resource units must equal sum across all jobs: 127."""
        assert report_data["total_resource_units"] == 127, (
            f"Expected 127 total resource units, got "
            f"{report_data['total_resource_units']}."
        )

    def test_per_type_gpu_total(self, report_data):
        """GPU worker type must account for 60 resource units total."""
        assert report_data["per_type_totals"].get("gpu") == 60

    def test_batch_snapshots_independent(self, report_data):
        """Each batch snapshot must reflect only that batch's allocation.

        The resource tracker should not accumulate across batches — each
        snapshot in batch_snapshots is the resource usage for that single
        batch only. Check /app/runtime/resource_tracker.py for running
        totals that should be per-batch instead.
        """
        snapshots = report_data["batch_snapshots"]
        # First batch should have less than 12 total units (one batch worth)
        first_batch_total = sum(snapshots[0].values())
        assert first_batch_total <= 12, (
            f"First batch snapshot has {first_batch_total} total units but "
            f"batch capacity is 12. Snapshots should show per-batch "
            f"allocation, not cumulative totals. Check accumulation logic "
            f"in /app/runtime/resource_tracker.py."
        )

    def test_snapshot_count_matches_batches(self, report_data):
        """Number of batch snapshots must equal batch count."""
        assert len(report_data["batch_snapshots"]) == report_data["batch_count"]


class TestDeadlineTiming:
    """Validates deadline checker computes batch timing correctly."""

    def test_total_duration(self, manifest_data):
        """Total scheduled duration must be 1270 time units.

        With deadline_window=10 and total resources=127:
        duration = sum(window * batch_resource_units) = 10 * 127 = 1270.
        Check /app/runtime/deadline_checker.py for off-by-one errors
        in the duration calculation.
        """
        timing = manifest_data["timing"]
        assert timing["total_duration"] == 1270, (
            f"Expected total_duration=1270, got {timing['total_duration']}. "
            f"Check duration formula in /app/runtime/deadline_checker.py — "
            f"should be deadline_window * total_resource_units per batch "
            f"with no extra offset."
        )

    def test_first_batch_start_time(self, manifest_data):
        """First batch must start at reference time 1700000500."""
        timing = manifest_data["timing"]
        assert timing["batch_timing"][0]["start_time"] == 1700000500

    def test_batch_timing_continuity(self, manifest_data):
        """Each batch must start where the previous batch ends."""
        timing = manifest_data["timing"]
        for i in range(1, len(timing["batch_timing"])):
            prev_end = timing["batch_timing"][i - 1]["end_time"]
            curr_start = timing["batch_timing"][i]["start_time"]
            assert prev_end == curr_start, (
                f"Batch {i} starts at {curr_start} but previous batch "
                f"ends at {prev_end}. Timing must be continuous."
            )
