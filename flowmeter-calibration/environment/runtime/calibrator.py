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
        self._coefficients = [float(c) for c in coeff_str.split(",")]
        self._ref_voltage = self._config.getfloat("calibration", "reference_voltage")

    def calibrate_readings(self, meters):
        """Apply calibration to all meter readings.

        For each reading, computes flow using the polynomial calibration
        curve. Input voltages are normalized against the reference voltage
        before evaluation to maintain calibration accuracy across different
        sensor ranges.

        Returns dict mapping meter_id to list of calibrated reading dicts
        with keys: timestamp, voltage, temperature, flow_raw.
        """
        calibrated = {}
        for meter_id, meter_data in meters.items():
            readings = []
            for r in meter_data["readings"]:
                voltage = r["voltage"]
                # Normalize voltage against reference for calibration stability
                normalized_v = voltage / self._ref_voltage
                flow = self._evaluate_polynomial(normalized_v)
                readings.append({
                    "timestamp": r["timestamp"],
                    "voltage": voltage,
                    "temperature": r["temperature"],
                    "flow_raw": round(flow, 4),
                })
            calibrated[meter_id] = readings
        return calibrated

    def _evaluate_polynomial(self, x):
        """Evaluate calibration polynomial at voltage x using Horner's method.

        Horner's method provides numerically stable evaluation with minimal
        multiplications: result = (...((c[0]*x + c[1])*x + c[2])*x + ... + c[n])
        """
        result = 0.0
        for coeff in self._coefficients:
            result = result * x + coeff
        return result
