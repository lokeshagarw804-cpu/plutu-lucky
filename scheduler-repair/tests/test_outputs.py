"""
Verification tests for the job scheduler.
Checks that schedule.json and report.json contain correct values.
"""

import json
import os
import pytest


SCHEDULE_PATH = "/app/runtime/output/schedule.json"
REPORT_PATH = "/app/runtime/output/report.json"


@pytest.fixture
def schedule():
    assert os.path.isfile(SCHEDULE_PATH), f"Missing {SCHEDULE_PATH}"
    with open(SCHEDULE_PATH, "r") as f:
        return json.load(f)


@pytest.fixture
def report():
    assert os.path.isfile(REPORT_PATH), f"Missing {REPORT_PATH}"
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


# --- Structure tests (easy) ---

def test_schedule_file_exists():
    assert os.path.isfile(SCHEDULE_PATH)


def test_report_file_exists():
    assert os.path.isfile(REPORT_PATH)


def test_schedule_is_list(schedule):
    assert isinstance(schedule, list)


def test_schedule_entry_fields(schedule):
    required_fields = {"job_id", "worker", "start_ms", "finish_ms", "on_time"}
    for entry in schedule:
        assert required_fields.issubset(entry.keys()), f"Missing fields in {entry}"


def test_schedule_has_24_entries(schedule):
    assert len(schedule) == 24


def test_report_has_required_keys(report):
    for key in ["total_jobs", "on_time_count", "violation_count", "worker_utilization"]:
        assert key in report, f"Missing key: {key}"


# --- Priority ordering test (catches Bug 1) ---

def test_high_priority_jobs_scheduled_first(schedule):
    """High-priority jobs (H*) must appear before low-priority jobs (L*) in schedule."""
    job_ids = [entry["job_id"] for entry in schedule]
    last_high_idx = max(i for i, jid in enumerate(job_ids) if jid.startswith("H"))
    first_low_idx = min(i for i, jid in enumerate(job_ids) if jid.startswith("L"))
    assert last_high_idx < first_low_idx, (
        f"Priority inversion: last H-job at index {last_high_idx}, "
        f"first L-job at index {first_low_idx}"
    )


# --- Deadline correctness tests (catches Bug 2) ---

def test_on_time_count(report):
    assert report["on_time_count"] == 22


def test_violation_count(report):
    assert report["violation_count"] == 2


def test_exact_deadline_jobs_are_on_time(schedule):
    """Jobs finishing exactly at their deadline should be marked on_time=True."""
    exact_deadline_jobs = {"H001", "H002", "M003", "M001", "M002"}
    for entry in schedule:
        if entry["job_id"] in exact_deadline_jobs:
            assert entry["on_time"] is True, (
                f"{entry['job_id']} finishes at deadline but marked not on_time"
            )


# --- Utilization tests (catches Bug 3) ---

def test_worker_a_utilization(report):
    util = report["worker_utilization"]
    assert abs(util["worker_a"] - 0.99) < 0.001


def test_worker_b_utilization(report):
    util = report["worker_utilization"]
    assert abs(util["worker_b"] - 1.19) < 0.001


def test_worker_c_utilization(report):
    util = report["worker_utilization"]
    assert abs(util["worker_c"] - 0.72) < 0.001


# --- Combined correctness test ---

def test_total_jobs(report):
    assert report["total_jobs"] == 24
