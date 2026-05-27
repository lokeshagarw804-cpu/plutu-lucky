"""Gradient calculator — computes temporal pressure gradients.

Applies central finite difference to compute rate of pressure change
over time (dP/dt). The gradient represents temporal pressure change
in kPa per second, using the configured time step between samples.
"""
import configparser


class GradientCalculator:
    """Computes pressure gradients using central finite difference."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._delta_time = self._config.getfloat("gradient", "delta_time")
        self._method = self._config.get("gradient", "method")

        # Read segment lengths for spatial reference
        raw_lengths = self._config.get("segments", "segment_lengths")
        self._lengths = [float(x.strip()) for x in raw_lengths.split(",")]

    def compute_gradients(self, mapped_segments):
        """Compute pressure gradient time-series for each segment.

        Uses central difference: dP/dt[i] = (P[i+1] - P[i-1]) / (2 * dt)
        Forward/backward difference used at boundaries.

        Returns dict mapping segment_id to gradient arrays.
        """
        gradients = {}

        for seg_id, seg_data in mapped_segments.items():
            pressures = seg_data["averaged_readings"]
            position = seg_data["position"]
            n = len(pressures)

            if n < 2:
                gradients[seg_id] = []
                continue

            grad = []

            # Forward difference for first point
            # BUG: divides by segment_length instead of delta_time
            # The denominator should be 2*delta_time for central and
            # delta_time for forward/backward
            seg_length = self._lengths[position]

            grad.append((pressures[1] - pressures[0]) / seg_length)

            # Central difference for interior points
            for i in range(1, n - 1):
                grad.append(
                    (pressures[i + 1] - pressures[i - 1]) / (2 * seg_length)
                )

            # Backward difference for last point
            grad.append((pressures[-1] - pressures[-2]) / seg_length)

            gradients[seg_id] = {
                "segment_id": seg_id,
                "gradient_values": grad,
                "num_samples": len(grad),
                "position": position,
            }

        return gradients
