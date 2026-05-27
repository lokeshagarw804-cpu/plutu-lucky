"""Audit trail writer — produces execution schedule and audit output.

Serializes the computed schedule and node metadata to JSON output files
for downstream consumption and compliance auditing.
"""
import json
import os


class AuditWriter:
    """Writes execution schedule and audit trail to output directory."""

    def __init__(self, output_dir):
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def write_schedule(self, schedule, prioritizer, graph_data, scheduler):
        """Write execution schedule and audit trail.

        Produces two files:
        - execution_schedule.json: slot assignments and node metadata
        - audit_trail.json: summary statistics and scheduling decisions
        """
        nodes = {n["node_id"]: n for n in graph_data["nodes"]}

        # Build schedule output
        slots = []
        for idx, slot_nodes in enumerate(schedule):
            slot_entries = []
            for node_id in slot_nodes:
                slot_entries.append({
                    "node_id": node_id,
                    "priority": nodes[node_id]["priority"],
                    "effective_priority": prioritizer.get_effective_priority(node_id),
                    "depth": prioritizer.get_depth(node_id),
                    "critical_cost": prioritizer.get_critical_cost(node_id),
                    "cost": nodes[node_id]["cost"],
                })
            slots.append({
                "slot_index": idx,
                "nodes": sorted(slot_entries, key=lambda e: e["node_id"]),
                "node_count": len(slot_entries),
            })

        schedule_output = {
            "workflow_id": graph_data["workflow_id"],
            "total_nodes": len(nodes),
            "total_slots": len(schedule),
            "max_parallelism": scheduler.get_max_parallelism(),
            "slots": slots,
        }

        # Build audit trail
        scheduled_node_ids = []
        for slot in schedule:
            scheduled_node_ids.extend(slot)

        unscheduled = [nid for nid in nodes if nid not in scheduled_node_ids]

        audit_output = {
            "workflow_id": graph_data["workflow_id"],
            "total_nodes": len(nodes),
            "scheduled_count": len(scheduled_node_ids),
            "unscheduled_count": len(unscheduled),
            "unscheduled_nodes": sorted(unscheduled),
            "slot_count": len(schedule),
            "max_parallelism_used": scheduler.get_max_parallelism(),
            "critical_nodes": sorted([
                nid for nid, n in nodes.items()
                if n["priority"] == "critical"
            ]),
        }

        schedule_path = os.path.join(self._output_dir, "execution_schedule.json")
        audit_path = os.path.join(self._output_dir, "audit_trail.json")

        with open(schedule_path, "w") as f:
            json.dump(schedule_output, f, indent=2)

        with open(audit_path, "w") as f:
            json.dump(audit_output, f, indent=2)
