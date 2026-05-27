"""Incident detector — identifies sustained performance degradation.

Scans the ranked percentile scores for each node and identifies
sequences of consecutive windows where a node's degradation percentile
exceeds the configured threshold. Such sequences are flagged as
performance degradation incidents.
"""
import configparser


class IncidentDetector:
    """Detects sustained degradation incidents from ranked scores."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._threshold = self._config.getfloat("detection", "degradation_threshold")
        self._min_windows = self._config.getint("detection", "min_consecutive_windows")

    def detect_incidents(self, ranked):
        """Find degradation incidents across all nodes.

        A degradation incident is a sequence of consecutive windows
        where a node's percentile rank exceeds the threshold for at
        least min_consecutive_windows windows.

        Args:
            ranked: dict of node_id -> list of {window_idx, raw_score, percentile_rank}

        Returns:
            list of incident dicts with node_id, start_window, end_window,
            duration_windows, peak_score, and severity.
        """
        incidents = []

        for node_id, windows in ranked.items():
            run_start = None
            run_length = 0
            peak_score = 0.0

            for w in windows:
                pct = w["percentile_rank"]
                if pct > self._threshold:
                    if run_start is None:
                        run_start = w["window_idx"]
                    run_length += 1
                    peak_score = max(peak_score, pct)
                else:
                    if run_length >= self._min_windows:
                        severity = self._compute_severity(
                            peak_score, run_length
                        )
                        incidents.append({
                            "node_id": node_id,
                            "start_window": run_start,
                            "end_window": run_start + run_length - 1,
                            "duration_windows": run_length,
                            "peak_score": peak_score,
                            "severity": severity,
                        })
                    run_start = None
                    run_length = 0
                    peak_score = 0.0

            # Check final run
            if run_length >= self._min_windows:
                severity = self._compute_severity(peak_score, run_length)
                incidents.append({
                    "node_id": node_id,
                    "start_window": run_start,
                    "end_window": run_start + run_length - 1,
                    "duration_windows": run_length,
                    "peak_score": peak_score,
                    "severity": severity,
                })

        return incidents

    def _compute_severity(self, peak_score, duration):
        """Compute incident severity from peak score and duration.

        Severity formula: peak_score * (1 + log2(duration) * 0.1)
        Capped at 1.0.

        Args:
            peak_score: highest percentile rank during incident
            duration: number of consecutive windows

        Returns:
            Severity score in [0, 1]
        """
        import math
        severity = peak_score * (1 + math.log2(max(1, duration)) * 0.1)
        return round(min(severity, 1.0), 4)
