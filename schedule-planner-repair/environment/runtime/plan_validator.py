"""Plan validator — compares execution results against progress snapshots.

The validation process checks that the executor's final job states
are consistent with the periodic progress snapshots captured during
scheduling. Any discrepancies indicate scheduling logic errors.
"""
import configparser


class PlanValidator:
    """Compares final execution state with progress snapshot history."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        # Tolerance for comparing execution vs snapshot progress
        self._tolerance = self._config.getint(
            "scheduler", "validation_tolerance_ms"
        )

    def validate(self, execution_results, snapshots):
        """Compare final execution state against last progress snapshot.

        Returns validation report with per-job comparison.
        Uses configured tolerance for comparing execution times.
        """
        report = {
            "total_jobs": len(execution_results),
            "validated_jobs": 0,
            "mismatches": [],
            "status": "valid",
        }

        if not snapshots:
            report["status"] = "no_snapshots"
            return report

        last_snapshot = snapshots[-1]
        snapshot_progress = last_snapshot["execution_progress"]

        for state in execution_results:
            jid = state["job_id"]
            final_ms = state["executed_ms"]
            snap_ms = snapshot_progress.get(jid, 0)

            diff = abs(final_ms - snap_ms)
            if diff <= self._tolerance:
                report["validated_jobs"] += 1
            else:
                report["mismatches"].append({
                    "job_id": jid,
                    "executor_ms": final_ms,
                    "snapshot_ms": snap_ms,
                    "difference_ms": diff,
                })

        if report["mismatches"]:
            report["status"] = "mismatches_found"

        return report
