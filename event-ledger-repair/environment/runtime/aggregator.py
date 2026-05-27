"""Window aggregator — computes per-window balance snapshots.

Groups events into time windows and computes running balance state
for each account stream within each window. The final snapshot of
each window represents the account state at window close.
"""
import configparser


class WindowAggregator:
    """Aggregates events into time-windowed balance snapshots."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_duration = self._config.getint(
            "reconciliation", "window_duration_seconds"
        )
        self._batch_size = self._config.getint("ledger", "batch_size")

    def aggregate(self, sorted_events):
        """Compute per-window balance snapshots from sorted events.

        Events are grouped into fixed-duration time windows. For each
        stream within a window, the running balance is tracked. Each
        window snapshot holds the balance state at window close.

        Returns list of window dicts with per-stream balances.
        """
        if not sorted_events:
            return []

        # Determine time range
        first_ts = sorted_events[0]["timestamp"]
        last_ts = sorted_events[-1]["timestamp"]

        # Calculate window boundaries
        start_window = (first_ts // self._window_duration) * self._window_duration
        windows = []
        current_start = start_window

        while current_start <= last_ts:
            windows.append({
                "window_start": current_start,
                "window_end": current_start + self._window_duration,
                "balances": {},
                "event_count": 0,
            })
            current_start += self._window_duration

        # Process events in batches and accumulate into windows
        running_balances = {}

        for i in range(0, len(sorted_events), self._batch_size):
            batch = sorted_events[i:i + self._batch_size]
            batch_snapshots = self._process_batch(batch, running_balances)

            # Merge batch results into window snapshots
            for snapshot in batch_snapshots:
                win_idx = self._find_window(snapshot["timestamp"], windows)
                if win_idx is not None:
                    windows[win_idx]["event_count"] += 1
                    stream = snapshot["stream_id"]
                    # Update window balance from batch snapshot
                    if stream not in windows[win_idx]["balances"]:
                        windows[win_idx]["balances"][stream] = 0.0
                    windows[win_idx]["balances"][stream] += snapshot["balance"]

        return windows

    def _process_batch(self, batch, running_balances):
        """Process a batch of events updating running balances.

        Returns list of snapshot dicts with balance after each event.
        """
        snapshots = []

        for event in batch:
            stream = event["stream_id"]
            if stream not in running_balances:
                running_balances[stream] = 0.0

            if event["type"] == "deposit":
                running_balances[stream] += event["amount"]
            elif event["type"] == "withdrawal":
                running_balances[stream] -= event["amount"]

            snapshots.append({
                "stream_id": stream,
                "timestamp": event["timestamp"],
                "balance": running_balances[stream],
                "event_id": event["event_id"],
            })

        return snapshots

    def _find_window(self, timestamp, windows):
        """Find window index for a given timestamp."""
        for idx, win in enumerate(windows):
            if win["window_start"] <= timestamp < win["window_end"]:
                return idx
        return None
