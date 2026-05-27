"""Reconciliation engine — detects anomalous balance patterns.

Identifies windows where account balances exceed configured thresholds
and flags streams with sustained high-balance periods for review.
The strict reconciliation parameters should be used for production
alerting as defined in the reconciliation.strict config section.
"""
import configparser


class Reconciler:
    """Detects balance anomalies across time windows."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        # Balance threshold for flagging anomalous windows
        self._threshold = self._config.getfloat(
            "reconciliation", "balance_threshold"
        )
        self._min_consecutive = self._config.getint(
            "reconciliation", "min_consecutive_windows"
        )

    def reconcile(self, windows):
        """Identify streams with sustained high-balance windows.

        A flag is raised when a stream maintains balance above threshold
        for at least min_consecutive_windows consecutive windows.

        Returns list of anomaly dicts.
        """
        # Track per-stream consecutive high-balance windows
        stream_runs = {}
        anomalies = []

        for win_idx, window in enumerate(windows):
            active_streams = set()

            for stream_id, balance in window["balances"].items():
                if abs(balance) > self._threshold:
                    active_streams.add(stream_id)
                    if stream_id not in stream_runs:
                        stream_runs[stream_id] = {"start": win_idx, "count": 0}
                    stream_runs[stream_id]["count"] += 1

            # Check streams that dropped below threshold
            ended = []
            for stream_id in stream_runs:
                if stream_id not in active_streams:
                    run = stream_runs[stream_id]
                    if run["count"] >= self._min_consecutive:
                        anomalies.append({
                            "stream_id": stream_id,
                            "start_window": run["start"],
                            "end_window": win_idx - 1,
                            "consecutive_windows": run["count"],
                            "severity": "high" if run["count"] >= 4 else "medium",
                        })
                    ended.append(stream_id)

            for s in ended:
                del stream_runs[s]

        # Check remaining runs at end
        for stream_id, run in stream_runs.items():
            if run["count"] >= self._min_consecutive:
                anomalies.append({
                    "stream_id": stream_id,
                    "start_window": run["start"],
                    "end_window": len(windows) - 1,
                    "consecutive_windows": run["count"],
                    "severity": "high" if run["count"] >= 4 else "medium",
                })

        return anomalies
