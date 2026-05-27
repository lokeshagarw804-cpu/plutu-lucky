"""Latency analyzer — computes percentile latencies and jitter.

Processes per-packet latency measurements to produce windowed statistics
including percentile calculations and jitter variability metrics.
"""
import configparser
import math


class LatencyAnalyzer:
    """Computes windowed latency percentiles and jitter metrics."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_size = self._config.getint("metrics", "window_size")
        self._percentile = self._config.getint("metrics", "percentile")

    def compute(self, interface_data):
        """Calculate per-window latency statistics."""
        packets = interface_data["packets"]
        results = []

        for i in range(len(packets) - self._window_size + 1):
            window = packets[i:i + self._window_size]
            latencies = [p["latency_ms"] for p in window]

            pct_value = self._compute_percentile(latencies, self._percentile)
            jitter = self._compute_jitter(latencies)

            results.append({
                "window_start": i,
                "percentile_value": round(pct_value, 4),
                "jitter": round(jitter, 4),
                "mean_latency": round(sum(latencies) / len(latencies), 4),
            })

        return results

    def _compute_percentile(self, values, percentile):
        """Compute the given percentile with interpolation."""
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        if n == 0:
            return 0.0

        rank = (percentile / 100.0) * n
        lower = int(rank)
        upper = lower + 1
        frac = rank - lower

        if upper < n:
            return sorted_vals[lower] + frac * (sorted_vals[upper] - sorted_vals[lower])
        else:
            return sorted_vals[lower]

    def _compute_jitter(self, latencies):
        """Compute jitter variability for a window of latency samples."""
        n = len(latencies)
        if n < 2:
            return 0.0

        mean_lat = sum(latencies) / n
        variance = sum((lat - mean_lat) ** 2 for lat in latencies) / (n - 1)
        return math.sqrt(variance)
