"""Validation tests for preemptive priority scheduling engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
PLAN_PATH = os.path.join(OUTPUT_DIR, "execution_plan.json")
SNAPSHOTS_PATH = os.path.join(OUTPUT_DIR, "progress_snapshots.json")
VALIDATION_PATH = os.path.join(OUTPUT_DIR, "validation_report.json")


@pytest.fixture(scope="module")
def plan_data():
    """Load execution plan output."""
    with open(PLAN_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def snapshots_data():
    """Load progress snapshots output."""
    with open(SNAPSHOTS_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def validation_data():
    """Load validation report output."""
    with open(VALIDATION_PATH, "r") as f:
        return json.load(f)


class TestOutputFileStructure:
    """Basic output file existence and structure validation."""

    def test_execution_plan_file_exists(self):
        """Execution plan output file must be generated."""
        assert os.path.isfile(PLAN_PATH)

    def test_progress_snapshots_file_exists(self):
        """Progress snapshots output file must be generated."""
        assert os.path.isfile(SNAPSHOTS_PATH)

    def test_validation_report_file_exists(self):
        """Validation report output file must be generated."""
        assert os.path.isfile(VALIDATION_PATH)

    def test_execution_plan_structure(self, plan_data):
        """Execution plan output must contain required fields."""
        assert "total_jobs_scheduled" in plan_data
        assert "total_queues" in plan_data
        assert "jobs_completed" in plan_data
        assert "deadlines_met" in plan_data
        assert "execution_results" in plan_data
        assert "queues_loaded" in plan_data


class TestQueueLoading:
    """Validates that all configured queues are loaded correctly."""

    def test_all_queues_loaded(self, plan_data):
        """All 4 configured queues must be loaded including maintenance."""
        loaded = plan_data["queues_loaded"]
        assert len(loaded) == 4, (
            f"Expected 4 queues but got {len(loaded)}: {loaded}. "
            f"Check queue filtering in /app/runtime/queue_loader.py — "
            f"verify how active_queues config value is parsed."
        )

    def test_maintenance_queue_present(self, plan_data):
        """The maintenance queue must be included in loaded queues."""
        loaded = plan_data["queues_loaded"]
        assert "maintenance" in loaded, (
            f"Queue 'maintenance' missing from loaded queues: {loaded}. "
            f"Check how /app/runtime/queue_loader.py splits the "
            f"active_queues configuration value."
        )

    def test_total_job_count(self, plan_data):
        """Must schedule exactly 50 jobs from all 4 queues."""
        assert plan_data["total_jobs_scheduled"] == 50, (
            f"Expected 50 jobs but scheduled "
            f"{plan_data['total_jobs_scheduled']}. "
            f"Missing jobs likely from a queue not being loaded."
        )


class TestExecutionResults:
    """Validates execution completion and deadline compliance."""

    def test_queue_count(self, plan_data):
        """Must report exactly 4 loaded queues."""
        assert plan_data["total_queues"] == 4

    def test_completed_job_count(self, plan_data):
        """Correct number of jobs must complete within max_rounds."""
        assert plan_data["jobs_completed"] == 43, (
            f"Expected 43 completed jobs but got "
            f"{plan_data['jobs_completed']}. "
            f"With quantum=100ms and max_rounds=10, jobs needing "
            f"over 1000ms cannot complete. Verify all queues are loaded."
        )

    def test_deadlines_met_count(self, plan_data):
        """Correct number of jobs must meet their deadlines."""
        assert plan_data["deadlines_met"] == 43, (
            f"Expected 43 deadlines met but got "
            f"{plan_data['deadlines_met']}. "
            f"Check that priority sorting in /app/runtime/priority_sorter.py "
            f"produces fully deterministic ordering when multiple jobs "
            f"share the same priority and deadline values."
        )

    def test_execution_results_count(self, plan_data):
        """Execution results must contain an entry for every scheduled job."""
        assert len(plan_data["execution_results"]) == 50


class TestProgressSnapshots:
    """Validates periodic progress snapshot correctness."""

    def test_snapshot_count(self, snapshots_data):
        """Must produce exactly 5 snapshots (10 rounds / 2 interval)."""
        assert snapshots_data["total_snapshots"] == 5, (
            f"Expected 5 snapshots but got {snapshots_data['total_snapshots']}. "
            f"With max_rounds=10 and interval=2, there should be 5 checkpoints."
        )

    def test_snapshot_progress_not_inflated(self, snapshots_data):
        """Snapshot progress values must not grow disproportionately."""
        snaps = snapshots_data["snapshots"]
        if len(snaps) >= 2:
            last_max = max(snaps[-1]["execution_progress"].values())
            # No single job should have more than max_rounds * quantum = 1000ms
            assert last_max <= 2000, (
                f"Last snapshot max progress is {last_max}ms, which is "
                f"unreasonably high. Check /app/runtime/deadline_checker.py — "
                f"snapshots should record point-in-time progress, not "
                f"accumulate across checkpoints."
            )

    def test_final_snapshot_matches_execution(self, snapshots_data, plan_data):
        """Last snapshot progress must be consistent with execution results."""
        snaps = snapshots_data["snapshots"]
        last_snap = snaps[-1]
        exec_results = plan_data["execution_results"]
        large_diffs = 0
        for result in exec_results:
            jid = result["job_id"]
            exec_ms = result["executed_ms"]
            snap_ms = last_snap["execution_progress"].get(jid, 0)
            # Executor may overshoot by up to one quantum (100ms)
            if abs(exec_ms - snap_ms) > 100:
                large_diffs += 1
        assert large_diffs == 0, (
            f"{large_diffs} jobs have execution/snapshot difference > 100ms. "
            f"Snapshots should track the same execution progress as "
            f"the executor within one quantum tolerance."
        )


class TestValidation:
    """Validates plan consistency checking correctness."""

    def test_validation_status_valid(self, validation_data):
        """Validation must report valid status with no mismatches."""
        assert validation_data["status"] == "valid", (
            f"Validation status is '{validation_data['status']}', "
            f"expected 'valid'. Check how /app/runtime/plan_validator.py "
            f"reads its tolerance configuration and ensure the snapshot "
            f"tracking in /app/runtime/deadline_checker.py is consistent "
            f"with execution."
        )

    def test_no_mismatches(self, validation_data):
        """Mismatch list must be empty when all bugs are fixed."""
        mismatches = validation_data["mismatches"]
        assert len(mismatches) == 0, (
            f"Found {len(mismatches)} mismatches: "
            f"{[m['job_id'] for m in mismatches[:5]]}. "
            f"Verify that progress snapshots accurately track execution "
            f"state and that the validator uses appropriate tolerance."
        )

    def test_all_jobs_validated(self, validation_data):
        """All jobs must be successfully validated."""
        assert validation_data["validated_jobs"] == 50, (
            f"Only {validation_data['validated_jobs']}/50 jobs "
            f"validated. Check validation tolerance precision."
        )
