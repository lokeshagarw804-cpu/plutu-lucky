"""Snapshot builder — creates periodic balance checkpoints.

During event replay, snapshots capture account state at regular
intervals (every N events). Snapshots record the balance of each
account at that checkpoint, representing a point-in-time view.
"""
import configparser
from collections import defaultdict


class SnapshotBuilder:
    """Builds periodic balance snapshots during event replay."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._interval = self._config.getint("snapshots", "interval_events")
        self._decimals = self._config.getint("projection", "decimal_places")

    def build_snapshots(self, sequenced_events):
        """Process events and capture snapshots at configured intervals.

        Returns list of snapshot dicts, each containing:
        - checkpoint_index: which snapshot number (0-based)
        - event_count: total events processed up to this point
        - balances: dict of account_id -> balance at this checkpoint
        """
        snapshots = []
        balances = {}
        cumulative = defaultdict(float)
        event_count = 0

        for event in sequenced_events:
            acct = event["account_id"]
            if acct not in balances:
                balances[acct] = 0.0

            amount = round(event["amount"], self._decimals)
            if event["event_type"] == "credit":
                balances[acct] = round(balances[acct] + amount, self._decimals)
            elif event["event_type"] == "debit":
                balances[acct] = round(balances[acct] - amount, self._decimals)

            event_count += 1

            if event_count % self._interval == 0:
                # Capture checkpoint state
                snapshot = {
                    "checkpoint_index": len(snapshots),
                    "event_count": event_count,
                    "balances": {},
                }
                for aid, bal in balances.items():
                    cumulative[aid] += bal
                    snapshot["balances"][aid] = cumulative[aid]
                snapshots.append(snapshot)

        return snapshots
