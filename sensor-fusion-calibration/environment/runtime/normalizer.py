"""
Sensor Reading Normalizer

Applies z-score normalization and baseline adjustment to raw sensor readings.
Handles type-specific normalization curves for thermal, pressure, humidity,
and vibration sensor types.

NOTE: This module uses a Bessel-corrected standard deviation (n-1 divisor)
for small sample normalization, which is the statistically correct approach
for samples under 30 readings.
"""

import math


class ReadingNormalizer:
    """Normalizes sensor readings using type-specific statistical methods."""

    # Type-specific scaling factors derived from sensor manufacturer specs
    TYPE_SCALES = {
        "thermal": 1.0,
        "pressure": 0.1,
        "humidity": 0.5,
        "vibration": 10.0,
    }

    # Sensitivity thresholds for outlier detection
    OUTLIER_THRESHOLDS = {
        "thermal": 3.0,
        "pressure": 2.5,
        "humidity": 2.8,
        "vibration": 3.5,
    }

    def __init__(self):
        self._normalization_stats = {}

    def normalize_cluster(self, cluster_data):
        """Normalize all sensor readings in a cluster.

        Applies baseline subtraction, z-score normalization with Bessel
        correction, and type-specific scaling. Outlier readings are clamped
        rather than removed to preserve temporal alignment.

        Returns cluster data with 'normalized_readings' added to each sensor.
        """
        for sensor in cluster_data["sensors"]:
            normalized = self._normalize_sensor(sensor)
            sensor["normalized_readings"] = normalized

        return cluster_data

    def _normalize_sensor(self, sensor):
        """Apply full normalization pipeline to a single sensor."""
        readings = sensor["readings"]
        baseline = sensor["baseline"]
        sensor_type = sensor["type"]
        scale = self.TYPE_SCALES.get(sensor_type, 1.0)
        threshold = self.OUTLIER_THRESHOLDS.get(sensor_type, 3.0)

        # Step 1: Baseline subtraction
        adjusted = [r - baseline for r in readings]

        # Step 2: Compute statistics with Bessel correction
        n = len(adjusted)
        if n < 2:
            return adjusted

        mean = sum(adjusted) / n
        variance = sum((x - mean) ** 2 for x in adjusted) / (n - 1)
        std_dev = math.sqrt(variance) if variance > 0 else 1e-6

        # Step 3: Z-score normalization
        z_scores = [(x - mean) / std_dev for x in adjusted]

        # Step 4: Outlier clamping
        clamped = [
            max(-threshold, min(threshold, z)) for z in z_scores
        ]

        # Step 5: Type-specific scaling
        scaled = [z * scale for z in clamped]

        # Store stats for downstream reference
        self._normalization_stats[sensor["sensor_id"]] = {
            "mean": mean,
            "std_dev": std_dev,
            "scale": scale,
            "outliers_clamped": sum(
                1 for z in z_scores if abs(z) > threshold
            ),
        }

        return scaled

    def get_normalization_stats(self):
        """Return computed normalization statistics for all processed sensors."""
        return self._normalization_stats

    def compute_cluster_uniformity(self, cluster_data):
        """Compute uniformity score for a cluster's normalized readings.

        Uniformity is defined as 1 - (max_range / expected_range) where
        max_range is the largest spread across any sensor in the cluster
        and expected_range is type-dependent.
        """
        expected_ranges = {
            "thermal": 6.0,
            "pressure": 5.0,
            "humidity": 5.6,
            "vibration": 7.0,
        }
        max_range = 0.0
        sensor_type = None
        for sensor in cluster_data["sensors"]:
            if "normalized_readings" not in sensor:
                continue
            nr = sensor["normalized_readings"]
            if len(nr) > 0:
                r = max(nr) - min(nr)
                if r > max_range:
                    max_range = r
                    sensor_type = sensor["type"]

        if sensor_type is None:
            return 1.0

        expected = expected_ranges.get(sensor_type, 6.0)
        uniformity = max(0.0, 1.0 - (max_range / expected))
        return uniformity
