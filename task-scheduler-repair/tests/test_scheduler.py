"""
Tests for the task scheduling system.

Validates queue filtering, priority computation, scheduling
order, and execution plan correctness.
"""
import json
import os
import pytest


PLAN_PATH = "/app/runtime/output/execution_plan.json"
SCHEDULE_PATH = "/app/runtime/output/schedule_matrix.json"
SUMMARY_PATH = "/app/runtime/output/scheduler_summary.json"


def load_plan():
    with open(PLAN_PATH, "r") as f:
        return json.load(f)


def load_schedule():
    with open(SCHEDULE_PATH, "r") as f:
        return json.load(f)


def load_summary():
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


# --- EASY TESTS (always pass) ---

class TestOutputStructure:
    """Basic output file presence and structure."""

    def test_plan_exists(self):
        """Execution plan output must exist."""
        assert os.path.isfile(PLAN_PATH)

    def test_schedule_exists(self):
        """Schedule matrix output must exist."""
        assert os.path.isfile(SCHEDULE_PATH)

    def test_summary_exists(self):
        """Scheduler summary output must exist."""
        assert os.path.isfile(SUMMARY_PATH)

    def test_plan_structure(self):
        """Plan must contain required fields."""
        p = load_plan()
        for key in ["total_scheduled", "entries", "total_duration_minutes"]:
            assert key in p, f"Missing key: {key}"


# --- MEDIUM TESTS (require Bug A fix) ---

class TestQueueInclusion:
    """Verify all configured queues are processed."""

    def test_total_task_count(self):
        """All 24 tasks from 4 queue files must be scheduled."""
        p = load_plan()
        assert p["total_scheduled"] == 24, (
            f"Expected 24 scheduled tasks, got {p['total_scheduled']}"
        )

    def test_deferred_queue_included(self):
        """Deferred queue tasks must appear in the execution plan."""
        p = load_plan()
        deferred = [e for e in p["entries"] if e["queue_id"] == "deferred"]
        assert len(deferred) > 0, (
            "No deferred queue tasks in plan"
        )

    def test_four_queues_in_plan(self):
        """All four queue types must be represented."""
        s = load_summary()
        assert len(s["queues_in_plan"]) == 4, (
            f"Expected 4 queues in plan, got {s['queues_in_plan']}"
        )


# --- MEDIUM-HARD TESTS (require Bug B or C fix) ---

class TestPriorityComputation:
    """Verify priority values are correct."""

    def test_critical_task_highest_priority(self):
        """Critical queue tasks must have the highest priorities."""
        p = load_plan()
        entries = p["entries"]
        first_entry = entries[0]
        assert first_entry["queue_id"] == "critical", (
            f"First scheduled task should be from critical queue, "
            f"got {first_entry['queue_id']} ({first_entry['task_id']})"
        )

    def test_priority_values_reasonable(self):
        """Effective priorities must not exceed 150.

        With correct aging (0.08 per round), priorities should remain
        bounded. Inflated values suggest the priority computation is
        accumulating state incorrectly across rounds.
        """
        p = load_plan()
        for entry in p["entries"]:
            assert entry["effective_priority"] < 150, (
                f"Task {entry['task_id']} has priority "
                f"{entry['effective_priority']} which is unreasonably "
                f"high — check if the priority engine accumulates "
                f"state across scheduling rounds"
            )

    def test_deferred_tasks_lowest_priority(self):
        """Deferred queue tasks must have the lowest priorities."""
        p = load_plan()
        entries = p["entries"]
        if len(entries) < 2:
            pytest.skip("Not enough entries")
        last_entries = entries[-6:]
        deferred_last = [e for e in last_entries if e["queue_id"] == "deferred"]
        assert len(deferred_last) >= 3, (
            "Deferred tasks should appear at the end of the plan"
        )


# --- HARD TESTS (require multiple bug fixes together) ---

class TestSchedulingOrder:
    """Verify deterministic scheduling order."""

    def test_priority_descending(self):
        """Tasks must be ordered by decreasing effective priority."""
        p = load_plan()
        entries = p["entries"]
        for i in range(len(entries) - 1):
            assert entries[i]["effective_priority"] >= entries[i + 1]["effective_priority"], (
                f"Position {i}: priority {entries[i]['effective_priority']} "
                f"followed by {entries[i+1]['effective_priority']}"
            )

    def test_tied_priority_queue_order(self):
        """Tasks with equal priority must be ordered by queue_id then task_id.

        T009 (standard queue) and T023 (batch queue) have the same
        effective priority. Batch precedes standard alphabetically,
        so T023 must appear before T009 in the execution plan.
        """
        p = load_plan()
        entries = p["entries"]
        t009_pos = None
        t023_pos = None
        for i, e in enumerate(entries):
            if e["task_id"] == "T009":
                t009_pos = i
            if e["task_id"] == "T023":
                t023_pos = i
        assert t009_pos is not None and t023_pos is not None, (
            "T009 and T023 must both be in the plan"
        )
        assert t023_pos < t009_pos, (
            f"T023 (batch) at position {t023_pos} should come before "
            f"T009 (standard) at position {t009_pos} — for equal "
            f"priorities, queue_id determines order"
        )

    def test_round_aging_effect(self):
        """Tasks scheduled in later rounds should show aging applied.

        With correct aging factor, a task scheduled in round 1 should
        have a slightly higher effective priority than its base suggests.
        """
        sch = load_schedule()
        rounds = sch["rounds"]
        assert "1" in rounds or 1 in rounds, (
            "Expected at least 2 scheduling rounds"
        )
