"""
Calibration Matrix Assembler

Constructs the final calibration matrix from confidence-scored sensor data.
Uses a sliding window approach to compute local calibration factors that
account for temporal variations in sensor behavior.

The matrix assembler produces per-sensor calibration vectors that can be
applied to future readings for real-time correction.
"""


class MatrixAssembler:
    """Assembles calibration vectors using sliding window analysis."""

    def __init__(self, config):
        self._window_size = config.getint("pipeline", "window_size")
        self._precision = config.getint("pipeline", "precision")

    def assemble(self, clusters, confidence_scores):
        """Assemble calibration matrix for all sensors across all clusters.

        For each sensor, computes a calibration vector by applying a sliding
        window of size W over the compensated readings and computing the
        local mean in each window position.

        The calibration factor at each position is weighted by the sensor's
        confidence score.

        Returns dict mapping sensor_id -> calibration_vector.
        """
        calibration_matrix = {}

        for cluster in clusters:
            for sensor in cluster["sensors"]:
                sensor_id = sensor["sensor_id"]
                confidence = confidence_scores.get(sensor_id, 0.0)

                if "compensated_readings" not in sensor:
                    continue

                readings = sensor["compensated_readings"]
                vector = self._compute_calibration_vector(
                    readings, confidence
                )
                calibration_matrix[sensor_id] = vector

        return calibration_matrix

    def _compute_calibration_vector(self, readings, confidence):
        """Compute calibration vector using sliding window local means.

        Window slides over the readings array, computing the mean of each
        window position. The calibration factor is the window mean multiplied
        by the confidence weight.
        """
        n = len(readings)
        window = self._window_size
        vector = []

        if n == 0:
            return vector

        for i in range(n):
            # Compute window boundaries
            start = max(0, i - window // 2)
            end = min(n, start + window)

            window_slice = readings[start:end]

            if window_slice:
                local_mean = sum(window_slice) / len(window_slice)
            else:
                local_mean = 0.0

            # Apply confidence weighting
            calibration_factor = local_mean * confidence

            vector.append(round(calibration_factor, self._precision))

        return vector

    def get_matrix_summary(self, calibration_matrix):
        """Compute summary statistics for the calibration matrix."""
        if not calibration_matrix:
            return {"sensor_count": 0, "avg_vector_length": 0}

        total_length = sum(len(v) for v in calibration_matrix.values())
        avg_length = total_length / len(calibration_matrix)

        all_values = []
        for vector in calibration_matrix.values():
            all_values.extend(vector)

        if all_values:
            return {
                "sensor_count": len(calibration_matrix),
                "avg_vector_length": avg_length,
                "value_range": [min(all_values), max(all_values)],
                "mean_value": sum(all_values) / len(all_values),
            }

        return {
            "sensor_count": len(calibration_matrix),
            "avg_vector_length": avg_length,
        }

    def validate_matrix(self, calibration_matrix):
        """Validate that all calibration vectors have expected length."""
        expected_length = None
        for sensor_id, vector in calibration_matrix.items():
            if expected_length is None:
                expected_length = len(vector)
            elif len(vector) != expected_length:
                return False, f"Inconsistent vector length for {sensor_id}"
        return True, "Matrix valid"
