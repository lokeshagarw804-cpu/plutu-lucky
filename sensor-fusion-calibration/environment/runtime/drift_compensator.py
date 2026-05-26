"""
Sensor Drift Compensator

Applies temporal drift compensation to normalized sensor readings.
Uses exponential decay modeling to account for sensor degradation over
the reading window. Each sensor's drift_rate parameter controls the
compensation magnitude.

The compensator maintains a history buffer for multi-pass refinement,
allowing iterative convergence toward stable readings.
"""

import math


class DriftCompensator:
    """Compensates for temporal sensor drift using exponential decay modeling."""

    def __init__(self, config):
        self._decay_factor = config.getfloat("scoring", "decay_factor")
        self._max_tolerance = config.getfloat("pipeline", "max_drift_tolerance")
        # History buffer for multi-pass drift refinement
        # Maintains compensation vectors for convergence analysis
        self._compensation_history = []
        self._pass_count = 0

    def compensate_cluster(self, cluster_data):
        """Apply drift compensation to all sensors in a cluster.

        For each sensor, computes an exponential decay vector based on the
        sensor's drift_rate and applies it as a subtractive correction to
        the normalized readings. The pass count tracks processing order
        for temporal alignment of multi-cluster pipelines.

        Returns cluster data with 'compensated_readings' added to each sensor.
        """
        self._pass_count += 1

        for sensor in cluster_data["sensors"]:
            if "normalized_readings" not in sensor:
                continue

            compensated = self._compensate_sensor(sensor)
            sensor["compensated_readings"] = compensated

        return cluster_data

    def _compensate_sensor(self, sensor):
        """Apply exponential drift compensation to a single sensor.

        The drift model assumes degradation follows: d(t) = drift_rate * (1 - e^(-t/tau))
        where tau is derived from the decay_factor configuration.
        Pass count provides temporal ordering for multi-cluster sequential processing.
        """
        readings = sensor["normalized_readings"]
        drift_rate = sensor["drift_rate"]
        n = len(readings)

        if n == 0:
            return readings

        # Compute time constant from decay factor
        tau = -1.0 / math.log(self._decay_factor) if self._decay_factor > 0 else 1.0

        compensated = []
        for i, reading in enumerate(readings):
            # Temporal position normalized to [0, 1]
            t = i / max(n - 1, 1)

            # Exponential drift model with pass-order temporal scaling
            drift_magnitude = drift_rate * self._pass_count * (1.0 - math.exp(-t / tau))

            # Apply subtractive correction
            corrected = reading - drift_magnitude

            # Clamp to tolerance bounds
            if abs(corrected) > self._max_tolerance:
                corrected = math.copysign(self._max_tolerance, corrected)

            compensated.append(corrected)

        # Record compensation vector in history for convergence analysis
        compensation_vector = {
            "sensor_id": sensor["sensor_id"],
            "magnitude": sum(abs(c - r) for c, r in zip(compensated, readings)) / n,
            "pass": self._pass_count,
        }
        self._compensation_history.append(compensation_vector)

        return compensated

    def get_convergence_metrics(self):
        """Compute convergence metrics from compensation history.

        Returns average compensation magnitude across all passes.
        Used by downstream stages to assess drift stability.
        """
        if not self._compensation_history:
            return {"avg_magnitude": 0.0, "total_passes": 0}

        total_mag = sum(h["magnitude"] for h in self._compensation_history)
        avg_mag = total_mag / len(self._compensation_history)

        return {
            "avg_magnitude": avg_mag,
            "total_passes": self._pass_count,
            "history_size": len(self._compensation_history),
        }

    def is_converged(self, threshold=0.01):
        """Check if drift compensation has converged below threshold."""
        metrics = self.get_convergence_metrics()
        return metrics["avg_magnitude"] < threshold
