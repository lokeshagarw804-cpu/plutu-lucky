"""Reconciler — compares projected balances against snapshot checkpoints.

The reconciliation process validates that the final projected state
is consistent with the periodic snapshots captured during replay.
Any discrepancies indicate event processing errors.
"""
import configparser


class Reconciler:
    """Compares final projected state with snapshot history."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        # Read rounding precision for reconciliation comparison
        self._decimals = self._config.getint("projection", "decimal_places")
        self._tolerance = self._config.getfloat(
            "projection.reconciliation", "tolerance"
        )

    def reconcile(self, final_balances, snapshots):
        """Compare final balances against last snapshot for consistency.

        Returns reconciliation report with per-account comparison.
        Uses configured decimal precision for rounding both sides.
        """
        report = {
            "total_accounts": len(final_balances),
            "reconciled_accounts": 0,
            "discrepancies": [],
            "status": "clean",
        }

        if not snapshots:
            report["status"] = "no_snapshots"
            return report

        last_snapshot = snapshots[-1]
        snapshot_balances = last_snapshot["balances"]

        for acct, final_bal in sorted(final_balances.items()):
            rounded_final = round(final_bal, self._decimals)
            snap_bal = snapshot_balances.get(acct, 0.0)
            rounded_snap = round(snap_bal, self._decimals)

            diff = abs(rounded_final - rounded_snap)
            if diff <= self._tolerance:
                report["reconciled_accounts"] += 1
            else:
                report["discrepancies"].append({
                    "account_id": acct,
                    "projected_balance": rounded_final,
                    "snapshot_balance": rounded_snap,
                    "difference": round(diff, self._decimals),
                })

        if report["discrepancies"]:
            report["status"] = "discrepancies_found"

        return report
