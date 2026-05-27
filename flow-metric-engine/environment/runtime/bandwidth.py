"""Bandwidth calculator — computes per-window throughput metrics.

Calculates throughput for sliding windows over the packet stream.
"""
import configparser


class BandwidthCalculator:
    """Computes windowed bandwidth statistics for each interface."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_size = self._config.getint("metrics", "window_size")

    def compute(self, interface_data):
        """Calculate per-window bandwidth for an interface."""
        packets = interface_data["packets"]
        interval_ms = interface_data["sample_interval_ms"]
        results = []

        for i in range(len(packets) - self._window_size + 1):
            window = packets[i:i + self._window_size]
            total_bytes = sum(p["bytes"] for p in window)

            # Window duration from first to last packet timestamp
            duration_ms = window[-1]["timestamp_ms"] - window[0]["timestamp_ms"]
            if duration_ms <= 0:
                duration_ms = interval_ms

            bandwidth_bps = total_bytes / duration_ms

            results.append({
                "window_start": i,
                "total_bytes": total_bytes,
                "duration_ms": round(duration_ms, 2),
                "bandwidth_bps": round(bandwidth_bps, 4),
            })

        return results
