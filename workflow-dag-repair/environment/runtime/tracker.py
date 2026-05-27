"""Resource tracker — monitors per-slot resource utilization.

Computes resource consumption for each time slot by tracking which
jobs are active. Reports usage statistics based on the configured
tracking mode for each resource pool.
"""
import configparser


class ResourceTracker:
    """Tracks and reports resource utilization across time slots."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_pools = self._config.get("resources", "resource_pools")
        self._pools = set(raw_pools.split(","))
        raw_limits = self._config.get("resources", "pool_limits")
        limit_values = [int(x.strip()) for x in raw_limits.split(",")]
        pool_names = list(raw_pools.split(","))
        self._limits = dict(zip(pool_names, limit_values))
        self._mode = self._config.get("resources", "tracking_mode")

    def compute_utilization(self, scheduled_jobs):
        """Compute per-slot resource usage from the scheduled job timeline.

        For each time slot, sums resource demands of all active jobs.
        Returns a dict with per-pool peak usage and slot-level breakdown.
        """
        if not scheduled_jobs:
            return {"pools": {}, "slot_breakdown": [], "total_slots": 0}

        max_slot = max(j["end_slot"] for j in scheduled_jobs)
        total_slots = max_slot + 1

        # Track usage per slot per pool
        slot_usage = {}
        for slot in range(total_slots):
            slot_usage[slot] = {pool: 0 for pool in self._pools}

        for job in scheduled_jobs:
            for slot in range(job["start_slot"], job["end_slot"] + 1):
                for resource, amount in job["resources"].items():
                    if resource in self._pools:
                        slot_usage[slot][resource] += amount

        # Compute peak usage per pool across all time slots
        peak_usage = {pool: 0 for pool in self._pools}
        for slot in range(total_slots):
            for pool in self._pools:
                peak_usage[pool] += slot_usage[slot][pool]

        # Compute utilization percentage against limits
        utilization = {}
        for pool in self._pools:
            limit = self._limits.get(pool, 1)
            utilization[pool] = {
                "peak_usage": peak_usage[pool],
                "limit": limit,
                "utilization_pct": round(peak_usage[pool] / limit * 100, 2),
            }

        # Slot breakdown
        slot_breakdown = []
        for slot in range(total_slots):
            slot_breakdown.append({
                "slot": slot,
                "usage": dict(slot_usage[slot]),
            })

        return {
            "pools": utilization,
            "slot_breakdown": slot_breakdown,
            "total_slots": total_slots,
        }
