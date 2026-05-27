"""Voltage-to-flow calibration — applies polynomial transfer function.

Converts raw voltage readings to flow rates (liters/min) using a
cubic polynomial calibration curve. Coefficients are loaded from
the configuration file.
"""
import configparser


class FlowCalibrator:
    """Applies polynomial calibration curve to voltage readings."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        coeff_str = self._config.get("calibration", "coefficients")
        # coefficients in config are listed low-order to high-order: a0,a1,a2,a3
        # so polynomial is: a0 + a1*x + a2*x^2 + a3*x^3
        self._coefficients = [float(c) for c in coeff_str.split(",")]

    def calibrate_readings(self, meters):
        """Apply calibration to all meter readings.

        For each reading, computes flow = sum(coeff[i] * voltage^i)
        using the polynomial coefficients.

        Returns dict mapping meter_id to list of calibrated reading dicts
        with keys: timestamp, voltage, temperature, flow_raw.
        """
        calibrated = {}
        for meter_id, meter_data in meters.items():
            readings = []
            for r in meter_data["readings"]:
                voltage = r["voltage"]
                flow = self._evaluate_polynomial(voltage)
                readings.append({
                    "timestamp": r["timestamp"],
                    "voltage": voltage,
                    "temperature": r["temperature"],
                    "flow_raw": round(flow, 4),
                })
            calibrated[meter_id] = readings
        return calibrated

    def _evaluate_polynomial(self, x):
        """Evaluate calibration polynomial at voltage x.

        Polynomial: a0 + a1*x + a2*x^2 + a3*x^3
        Coefficients stored as [a0, a1, a2, a3].
        """
        # BUG: evaluates in reversed coefficient order (high-to-low)
        # treating coefficients as [a3, a2, a1, a0] via Horner's method
        # This computes: ((a0*x + a1)*x + a2)*x + a3
        # instead of: a0 + a1*x + a2*x^2 + a3*x^3
        result = 0.0
        for coeff in self._coefficients:
            result = result * x + coeff
        return result
