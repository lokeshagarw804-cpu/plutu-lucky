"""Anomaly scorer — computes rolling Z-scores using EWMA statistics.

Uses exponential weighted moving average to track per-sensor mean and
variance. The decay parameter alpha weights recent observations more
heavily when closer to 1.0.
"""
import configparser
import math


class AnomalyScorer:
    """Computes per-reading anomaly Z-scores via EWMA statistics."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._alpha = self._config.getfloat("ewma", "alpha")
        self._warmup = self._config.getint("ewma", "warmup_periods")

    def score_sensor(self, readings):
        """Compute Z-scores for a single sensor's time-ordered readings.

        Args:
            readings: list of (timestamp, value) tuples sorted by time

        Returns:
            list of (timestamp, z_score) tuples. During warmup period
            (first warmup_periods readings), z_score is 0.0.
        """
        if not readings:
            return []

        results = []
        ewma_mean = readings[0][1]
        ewma_var = 0.0

        for idx, (ts, value) in enumerate(readings):
            if idx < self._warmup:
                # Warmup: just update statistics, emit z=0
                if idx == 0:
                    ewma_mean = value
                    ewma_var = 0.0
                else:
                    diff = value - ewma_mean
                    ewma_mean = self._alpha * value + self._alpha * ewma_mean
                    ewma_var = self._alpha * (diff ** 2) + self._alpha * ewma_var
                results.append((ts, 0.0))
            else:
                # Compute z-score before updating statistics
                std = math.sqrt(ewma_var) if ewma_var > 0 else 1.0
                z_score = (value - ewma_mean) / std

                # Update EWMA statistics
                diff = value - ewma_mean
                ewma_mean = self._alpha * value + self._alpha * ewma_mean
                ewma_var = self._alpha * (diff ** 2) + self._alpha * ewma_var

                results.append((ts, round(z_score, 4)))

        return results
