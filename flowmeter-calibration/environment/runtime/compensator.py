"""Temperature compensation — adjusts flow readings for thermal effects.

Applies linear temperature correction to raw flow values based on
temperature-dependent fluid viscosity changes. Higher temperatures
reduce viscosity and increase effective flow rate.
"""
import configparser


class TempCompensator:
    """Applies temperature-based correction to flow readings."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._factor = self._config.getfloat("compensation", "factor")
        self._ref_temp = self._config.getfloat("compensation", "reference_temp")

    def compensate(self, calibrated_meters):
        """Apply temperature compensation to all calibrated readings.

        The correction scales flow proportionally to thermal conditions.
        At reference temperature the correction is neutral (factor of 1.0).

        Returns dict mapping meter_id to list of compensated reading dicts
        with added key: flow_compensated.
        """
        compensated = {}
        for meter_id, readings in calibrated_meters.items():
            comp_readings = []
            for r in readings:
                temp = r["temperature"]
                flow_raw = r["flow_raw"]
                # Linear thermal correction based on operating temperature
                correction = 1.0 + self._factor * temp
                flow_comp = flow_raw * correction
                comp_readings.append({
                    **r,
                    "flow_compensated": round(flow_comp, 4),
                })
            compensated[meter_id] = comp_readings
        return compensated
