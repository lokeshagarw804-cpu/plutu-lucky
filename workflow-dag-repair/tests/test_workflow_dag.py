"""Validation tests for workflow DAG scheduler output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
SCHEDULE_PATH = os.path.join(OUTPUT_DIR, "execution_schedule.json")
AUDIT_PATH = os.path.join(OUTPUT_DIR, "audit_trail.json")


@pytest.fixture(scope="module")
def schedule_data():
    """Load execution schedule output."""
    with open(SCHEDULE_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def audit_data():
    """Load audit trail output."""
    with open(AUDIT_PATH, "r") as f:
        return json.load(f)


def find_node_in_schedule(schedule, node_id):
    """Find a node entry across all slots."""
    for slot in schedule["slots"]:
        for node in slot["nodes"]:
            if node["node_id"] == node_id:
                return node, slot["slot_index"]
    return None, None


class TestOutputStructure:
    """Basic output validation — file existence and structure."""

    def test_schedule_file_exists(self):
        """The execution_schedule.json file must be generated."""
        assert os.path.isfile(SCHEDULE_PATH), (
            f"Expected schedule output at {SCHEDULE_PATH}"
        )

    def test_audit_file_exists(self):
        """The audit_trail.json file must be generated."""
        assert os.path.isfile(AUDIT_PATH), (
            f"Expected audit output at {AUDIT_PATH}"
        )

    def test_schedule_has_required_fields(self, schedule_data):
        """Schedule must contain workflow_id, total_nodes, total_slots, slots."""
        for field in ("workflow_id", "total_nodes", "total_slots", "slots"):
            assert field in schedule_data, f"Missing field: {field}"
        assert isinstance(schedule_data["slots"], list)

    def test_audit_has_required_fields(self, audit_data):
        """Audit trail must contain documented metadata fields."""
        for field in ("workflow_id", "total_nodes", "scheduled_count",
                      "unscheduled_count", "unscheduled_nodes", "slot_count",
                      "max_parallelism_used", "critical_nodes"):
            assert field in audit_data, f"Missing field: {field}"


class TestScheduleCompleteness:
    """All workflow nodes must be scheduled — no orphaned tasks."""

    def test_all_nodes_scheduled(self, audit_data):
        """Every node in the workflow must appear in the schedule.

        If nodes are missing, the dependency resolution may be failing
        to advance past the initial wave of root nodes.
        """
        assert audit_data["scheduled_count"] == 15, (
            f"Expected 15 nodes scheduled but got "
            f"{audit_data['scheduled_count']}. "
            f"Unscheduled: {audit_data['unscheduled_nodes']}"
        )

    def test_no_unscheduled_nodes(self, audit_data):
        """The unscheduled node list must be empty."""
        assert audit_data["unscheduled_count"] == 0, (
            f"Found {audit_data['unscheduled_count']} unscheduled nodes: "
            f"{audit_data['unscheduled_nodes']}. Check that dependency "
            "state transitions allow downstream nodes to become ready."
        )


class TestParallelismConstraint:
    """Concurrency must respect the constrained configuration."""

    def test_max_parallelism_value(self, schedule_data):
        """Max parallelism must match the constrained scheduler config."""
        assert schedule_data["max_parallelism"] == 3, (
            f"Expected max_parallelism=3 but got "
            f"{schedule_data['max_parallelism']}."
        )

    def test_no_slot_exceeds_limit(self, schedule_data):
        """No time-slot may contain more than max_parallelism nodes."""
        limit = 3
        for slot in schedule_data["slots"]:
            assert slot["node_count"] <= limit, (
                f"Slot {slot['slot_index']} has {slot['node_count']} nodes, "
                f"exceeding the parallelism limit of {limit}."
            )

    def test_minimum_slot_count(self, schedule_data):
        """With 15 nodes and parallelism=3, need at least 5 slots
        (more due to dependency ordering constraints).
        """
        assert schedule_data["total_slots"] >= 7, (
            f"Expected at least 7 slots but got "
            f"{schedule_data['total_slots']}. With parallelism=3 and "
            "dependency chains, the schedule should span multiple waves."
        )


class TestCriticalPriority:
    """Nodes with critical priority must receive correct weight."""

    def test_critical_node_effective_priority(self, schedule_data):
        """Critical-priority nodes must have weight 8 as base (not default 1).

        The integration_tests node has priority=critical. Its effective
        priority should reflect the full critical weight, not the fallback.
        """
        node, slot_idx = find_node_in_schedule(schedule_data, "integration_tests")
        assert node is not None, "integration_tests not found in schedule"
        # With critical weight=8 and depth=2, decay=0.2, critical_cost=9
        # effective = 8*1.0 - 0.2 + 0.9 = 8.7
        assert node["effective_priority"] > 7.0, (
            f"integration_tests has effective_priority="
            f"{node['effective_priority']}, expected > 7.0 based on "
            "critical weight. Check that all priority level names are "
            "parsed correctly from the configuration."
        )

    def test_security_scan_boosted_priority(self, schedule_data):
        """security_scan has critical priority AND a 1.5x boost override."""
        node, _ = find_node_in_schedule(schedule_data, "security_scan")
        assert node is not None, "security_scan not found in schedule"
        # critical(8) * 1.5 boost - depth(1)*0.1 + cc(4)*0.1 = 12.3
        assert node["effective_priority"] > 10.0, (
            f"security_scan effective_priority={node['effective_priority']}, "
            "expected > 10.0 with critical weight and boost factor."
        )


class TestCriticalPathCost:
    """Critical path cost computation must use correct algorithm."""

    def test_integration_tests_critical_cost(self, schedule_data):
        """integration_tests depends on unit_tests_fe and unit_tests_be.

        The critical path cost should be the maximum predecessor chain,
        not the sum. Max(fe_chain=3+3=6, be_chain=4+5=9) → expected 9.
        """
        node, _ = find_node_in_schedule(schedule_data, "integration_tests")
        assert node is not None, "integration_tests not found"
        assert node["critical_cost"] == 9, (
            f"integration_tests critical_cost={node['critical_cost']}, "
            "expected 9. The critical path through a node should be the "
            "longest (maximum cost) predecessor chain, not the total."
        )

    def test_deploy_production_critical_cost(self, schedule_data):
        """deploy_production has deep dependency chains — cost must be max path."""
        node, _ = find_node_in_schedule(schedule_data, "deploy_production")
        assert node is not None, "deploy_production not found"
        # Longest chain: build_be(4) -> unit_tests_be(5) -> integration(6) ->
        # package(2) -> staging(3) -> smoke(2) = 22
        assert node["critical_cost"] == 22, (
            f"deploy_production critical_cost={node['critical_cost']}, "
            "expected 22."
        )


class TestDependencyOrdering:
    """Schedule must respect topological ordering of the DAG."""

    def test_build_before_tests(self, schedule_data):
        """Build nodes must appear in earlier slots than test nodes."""
        _, build_slot = find_node_in_schedule(schedule_data, "build_backend")
        _, test_slot = find_node_in_schedule(schedule_data, "unit_tests_be")
        assert build_slot is not None and test_slot is not None
        assert build_slot < test_slot, (
            f"build_backend in slot {build_slot} should precede "
            f"unit_tests_be in slot {test_slot}."
        )

    def test_deploy_ordering(self, schedule_data):
        """deploy_staging must precede deploy_production."""
        _, staging_slot = find_node_in_schedule(schedule_data, "deploy_staging")
        _, prod_slot = find_node_in_schedule(schedule_data, "deploy_production")
        assert staging_slot is not None and prod_slot is not None
        assert staging_slot < prod_slot, (
            f"deploy_staging (slot {staging_slot}) must precede "
            f"deploy_production (slot {prod_slot})."
        )

    def test_final_nodes_in_last_slot(self, schedule_data):
        """Terminal nodes (notify_team, update_docs) in the final slot."""
        _, notify_slot = find_node_in_schedule(schedule_data, "notify_team")
        _, docs_slot = find_node_in_schedule(schedule_data, "update_docs")
        last_slot = schedule_data["total_slots"] - 1
        assert notify_slot == last_slot, (
            f"notify_team in slot {notify_slot}, expected slot {last_slot}."
        )
        assert docs_slot == last_slot, (
            f"update_docs in slot {docs_slot}, expected slot {last_slot}."
        )
