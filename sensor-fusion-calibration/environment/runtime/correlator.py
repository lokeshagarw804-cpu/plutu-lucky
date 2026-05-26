"""
Cross-Sensor Correlation Engine

Computes pairwise correlation coefficients between sensors that share
cross-references. Uses Pearson correlation on compensated readings
to identify sensor clusters that are measuring related phenomena.

The correlation matrix is used downstream by the confidence scorer
to weight cross-referenced sensor contributions.
"""

import math


class CrossCorrelator:
    """Computes correlation coefficients between cross-referenced sensors."""

    def __init__(self):
        self._correlation_matrix = {}
        self._sensor_readings_cache = {}

    def build_correlation_matrix(self, clusters, cross_ref_map):
        """Build pairwise correlation matrix for all cross-referenced sensors.

        For each sensor pair (A, B) where B is in A's cross_refs,
        computes Pearson correlation coefficient between their
        compensated readings.

        Only sensors with valid compensated_readings are included.
        """
        # First pass: cache all compensated readings by sensor_id
        self._sensor_readings_cache = {}
        for cluster in clusters:
            for sensor in cluster["sensors"]:
                if "compensated_readings" in sensor:
                    self._sensor_readings_cache[sensor["sensor_id"]] = (
                        sensor["compensated_readings"]
                    )

        # Second pass: compute correlations for cross-referenced pairs
        for sensor_id, refs in cross_ref_map.items():
            if sensor_id not in self._sensor_readings_cache:
                continue

            readings_a = self._sensor_readings_cache[sensor_id]

            for ref_id in refs:
                if ref_id not in self._sensor_readings_cache:
                    continue

                readings_b = self._sensor_readings_cache[ref_id]
                correlation = self._pearson_correlation(readings_a, readings_b)

                # Store bidirectional correlation
                pair_key = tuple(sorted([sensor_id, ref_id]))
                self._correlation_matrix[pair_key] = correlation

        return self._correlation_matrix

    def _pearson_correlation(self, x, y):
        """Compute Pearson correlation coefficient between two sequences.

        Handles edge cases where variance is zero or sequences have
        different lengths (truncates to minimum length).
        """
        n = min(len(x), len(y))
        if n < 3:
            return 0.0

        x = x[:n]
        y = y[:n]

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        # Compute covariance and standard deviations
        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        var_x = sum((xi - mean_x) ** 2 for xi in x)
        var_y = sum((yi - mean_y) ** 2 for yi in y)

        denominator = math.sqrt(var_x * var_y)
        if denominator < 1e-10:
            return 0.0

        return cov / denominator

    def get_sensor_correlation_summary(self, sensor_id):
        """Get average correlation for a specific sensor with its references."""
        correlations = []
        for pair_key, corr in self._correlation_matrix.items():
            if sensor_id in pair_key:
                correlations.append(corr)

        if not correlations:
            return 0.0

        return sum(correlations) / len(correlations)

    def get_correlation_matrix(self):
        """Return the complete correlation matrix."""
        return self._correlation_matrix

    def get_highly_correlated_pairs(self, threshold=0.7):
        """Return sensor pairs with correlation above threshold."""
        return {
            pair: corr
            for pair, corr in self._correlation_matrix.items()
            if abs(corr) >= threshold
        }

    def get_matrix_density(self):
        """Compute density of the correlation matrix (non-zero entries ratio)."""
        total_entries = len(self._correlation_matrix)
        non_zero = sum(1 for v in self._correlation_matrix.values() if abs(v) > 0.01)
        if total_entries == 0:
            return 0.0
        return non_zero / total_entries
