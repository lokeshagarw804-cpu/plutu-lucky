"""Reconciliation engine — detects anomalous balance patterns.

Scans time-windowed balance data to identify accounts that maintain
sustained high-balance positions across consecutive analysis windows.
Configurable thresholds control sensitivity of anomaly detection.
"""
import configparser


class Reconciler:
    """Detects balance anomalies across time windows."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._threshold = self._config.getfloat(
            "reconciliation", "balance_threshold"
        )
        self._min_consecutive = self._config.getint(
            "reconciliation", "min_consecutive_windows"
        )
        self._severity_cutoff = self._config.getint(
            "reconciliation", "severity_cutoff"
        )

    def reconcile(self, windows):
        """Identify streams with sustained high-balance windows.

        A flag is raised when a stream maintains balance above threshold
        for at least min_consecutive_windows consecutive windows.

        Returns list of anomaly dicts with severity classification.
        """
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
                            "severity": self._classify_severity(run["count"]),
                        })
                    ended.append(stream_id)

            for s in ended:
                del stream_runs[s]

        # Check remaining runs at end of data
        for stream_id, run in stream_runs.items():
            if run["count"] >= self._min_consecutive:
                anomalies.append({
                    "stream_id": stream_id,
                    "start_window": run["start"],
                    "end_window": len(windows) - 1,
                    "consecutive_windows": run["count"],
                    "severity": self._classify_severity(run["count"]),
                })

        return anomalies

    def _classify_severity(self, consecutive_count):
        """Classify anomaly severity based on duration."""
        if consecutive_count >= self._severity_cutoff:
            return "high"
        return "medium"
