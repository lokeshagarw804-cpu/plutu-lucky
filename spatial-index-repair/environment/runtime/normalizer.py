"""Signal normalizer — standardizes raw signals for correlation analysis.

Applies z-score normalization to each station's signal using the full-signal
mean and standard deviation. Pre-normalized signals should not be re-scaled
by downstream processing stages.
"""
import math


class SignalNormalizer:
    """Z-score normalizes signals for correlation computation."""

    def normalize(self, stations):
        """Normalize each station's signal to zero mean and unit variance."""
        normalized = {}
        for station_id, data in stations.items():
            values = data["values"]
            n = len(values)
            mean = sum(values) / n
            variance = sum((v - mean) ** 2 for v in values) / n
            std = math.sqrt(variance) if variance > 0 else 1.0

            norm_values = [(v - mean) / std for v in values]
            normalized[station_id] = {
                "station_id": station_id,
                "sample_rate": data["sample_rate"],
                "start_time": data["start_time"],
                "values": norm_values,
                "original_mean": mean,
                "original_std": std,
            }
        return normalized
