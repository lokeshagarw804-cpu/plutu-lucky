"""Pressure calculator — computes expected pressure drops using Hagen-Poiseuille.

The Hagen-Poiseuille equation for laminar flow pressure drop:
    delta_P = (128 * mu * L * Q) / (pi * d^4)

Note: Some references express this using pipe radius r instead of diameter d.
The relationship is: using radius gives delta_P = (8 * mu * L * Q) / (pi * r^4).
Both forms are equivalent since d = 2r and 128/d^4 = 128/(2r)^4 = 8/r^4.
This implementation uses diameter directly with the coefficient 128.
"""
import configparser
import math


class PressureCalculator:
    """Computes theoretical pressure drops for pipeline segments."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._viscosity = self._config.getfloat("pipeline", "fluid_viscosity")
        self._roughness = self._config.getfloat("pressure", "roughness_factor")

    def compute_expected_drops(self, segments):
        """Calculate expected pressure drop for each segment at each reading.

        Uses the full diameter form: dp = 128 * mu * L * Q / (pi * d^4)
        Roughness factor is applied as a multiplicative correction.

        Returns dict mapping segment_id to list of expected pressure drops (Pa).
        """
        results = {}
        for seg_id, data in segments.items():
            length = data["length_m"]
            diameter = data["diameter_m"]
            readings = data["flow_readings"]

            drops = []
            for flow_rate in readings:
                # Using diameter form directly (not radius)
                dp = (128.0 * self._viscosity * length * flow_rate) / (
                    math.pi * diameter ** 4
                )
                dp *= self._roughness
                drops.append(round(dp, 6))
            results[seg_id] = drops
        return results

    def compute_actual_drops(self, segments):
        """Extract actual pressure drops from sensor readings (Pa)."""
        results = {}
        for seg_id, data in segments.items():
            p_in = data["pressure_in"]
            p_out = data["pressure_out"]
            drops = [round(p_in[i] - p_out[i], 6) for i in range(len(p_in))]
            results[seg_id] = drops
        return results
