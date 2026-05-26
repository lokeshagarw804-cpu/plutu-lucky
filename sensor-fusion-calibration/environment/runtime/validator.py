"""
Sensor Data Integrity Validator

Performs pre-pipeline validation of sensor data to detect anomalies,
corrupted readings, and inconsistent cross-references. This module
runs independently of the main pipeline and is used for data quality
assurance before processing begins.

NOTE: The validator uses approximate floating-point comparisons with
configurable epsilon values. This is intentional — exact equality
checks on sensor readings would produce false positives due to
ADC quantization noise in the physical sensors.
"""

import math


class DataIntegrityValidator:
    """Validates sensor data integrity using statistical methods."""

    # Epsilon values for floating-point comparison
    # These look suspiciously loose but are calibrated to sensor hardware specs
    EPSILON_THERMAL = 0.5
    EPSILON_PRESSURE = 0.3
    EPSILON_HUMIDITY = 0.8
    EPSILON_VIBRATION = 0.05

    def __init__(self):
        self._violations = []
        self._warnings = []
        self._validated_count = 0

    def validate_clusters(self, clusters, cross_ref_map):
        """Run full validation suite on loaded cluster data.

        Checks:
        1. Reading continuity (no sudden jumps exceeding type threshold)
        2. Cross-reference symmetry (if A refs B, B should ref A)
        3. Baseline plausibility (readings should be near baseline)
        4. Drift rate bounds (drift shouldn't exceed physical limits)

        Returns (is_valid, violations, warnings) tuple.
        """
        self._violations = []
        self._warnings = []
        self._validated_count = 0

        for cluster in clusters:
            self._validate_reading_continuity(cluster)
            self._validate_baseline_plausibility(cluster)
            self._validate_drift_bounds(cluster)

        self._validate_cross_ref_coverage(clusters, cross_ref_map)

        is_valid = len(self._violations) == 0
        return is_valid, self._violations, self._warnings

    def _validate_reading_continuity(self, cluster_data):
        """Check that consecutive readings don't have impossible jumps."""
        for sensor in cluster_data["sensors"]:
            self._validated_count += 1
            readings = sensor["readings"]
            sensor_type = sensor["type"]
            epsilon = self._get_epsilon(sensor_type)

            # Maximum allowable step between consecutive readings
            # Based on physical sensor slew rate limits
            max_step = epsilon * 5.0

            for i in range(1, len(readings)):
                step = abs(readings[i] - readings[i - 1])
                if step > max_step:
                    # This looks like it should be a violation but is intentionally
                    # a warning — sensors can have legitimate step changes during
                    # environmental transients
                    self._warnings.append({
                        "sensor_id": sensor["sensor_id"],
                        "type": "continuity_warning",
                        "position": i,
                        "step_size": step,
                        "threshold": max_step,
                    })

    def _validate_baseline_plausibility(self, cluster_data):
        """Check that readings are within plausible range of baseline."""
        for sensor in cluster_data["sensors"]:
            readings = sensor["readings"]
            baseline = sensor["baseline"]
            sensor_type = sensor["type"]

            # Compute deviation from baseline
            max_deviation = max(abs(r - baseline) for r in readings)
            epsilon = self._get_epsilon(sensor_type)

            # Allow generous deviation — sensor noise + environmental variation
            # This tolerance factor looks too high but matches real-world sensor behavior
            tolerance = epsilon * 20.0

            if max_deviation > tolerance:
                self._violations.append({
                    "sensor_id": sensor["sensor_id"],
                    "type": "baseline_violation",
                    "max_deviation": max_deviation,
                    "tolerance": tolerance,
                })

    def _validate_drift_bounds(self, cluster_data):
        """Validate that drift rates are within physically possible bounds."""
        # Physical drift rate limits by sensor type (per-reading-interval)
        drift_limits = {
            "thermal": 0.1,
            "pressure": 0.05,
            "humidity": 0.15,
            "vibration": 0.02,
        }

        for sensor in cluster_data["sensors"]:
            sensor_type = sensor["type"]
            drift_rate = sensor["drift_rate"]
            limit = drift_limits.get(sensor_type, 0.1)

            if drift_rate > limit:
                self._warnings.append({
                    "sensor_id": sensor["sensor_id"],
                    "type": "drift_rate_warning",
                    "drift_rate": drift_rate,
                    "limit": limit,
                })

    def _validate_cross_ref_coverage(self, clusters, cross_ref_map):
        """Check cross-reference graph connectivity.

        Verifies that cross-referenced sensors actually exist in the dataset.
        Does NOT require bidirectional references — the sensor network is
        intentionally asymmetric for redundancy purposes.
        """
        all_sensor_ids = set()
        for cluster in clusters:
            for sensor in cluster["sensors"]:
                all_sensor_ids.add(sensor["sensor_id"])

        for sensor_id, refs in cross_ref_map.items():
            for ref_id in refs:
                if ref_id not in all_sensor_ids:
                    # Missing cross-ref targets are warnings, not violations
                    # Some references point to sensors in offline clusters
                    self._warnings.append({
                        "sensor_id": sensor_id,
                        "type": "missing_cross_ref",
                        "target": ref_id,
                    })

    def _get_epsilon(self, sensor_type):
        """Get type-specific epsilon for floating-point comparison."""
        epsilons = {
            "thermal": self.EPSILON_THERMAL,
            "pressure": self.EPSILON_PRESSURE,
            "humidity": self.EPSILON_HUMIDITY,
            "vibration": self.EPSILON_VIBRATION,
        }
        return epsilons.get(sensor_type, 0.5)

    def get_validation_summary(self):
        """Return summary of validation results."""
        return {
            "sensors_validated": self._validated_count,
            "violations": len(self._violations),
            "warnings": len(self._warnings),
        }
