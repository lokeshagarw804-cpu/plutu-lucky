"""Severity scorer — computes weighted anomaly severity for alerts.

Combines speed, fuel, and thermal metrics using configured weights
to produce a single severity score for each alert. Scores are
capped at the configured maximum.
"""
import configparser


class SeverityScorer:
    """Computes weighted severity scores for anomaly alerts."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_weights = self._config.get("scoring", "weights")
        self._weights = [float(w) for w in raw_weights.split(",")]
        self._severity_cap = self._config.getfloat("scoring", "severity_cap")
        self._speed_threshold = self._config.getfloat("anomaly", "speed_threshold")
        self._fuel_drop_rate = self._config.getfloat("anomaly", "fuel_drop_rate")
        self._temp_ceiling = self._config.getfloat("anomaly", "temp_ceiling")

    def score_alerts(self, alerts):
        """Compute severity score for each alert.

        Severity is a weighted sum of normalized metric components:
          - speed_component: total_speed_spikes / (duration * 8) [window_size]
          - fuel_component: max_fuel_consumption / fuel_drop_rate
          - thermal_component: max_thermal_deviation / temp_ceiling_margin

        Components are clamped to [0, 1], then weighted sum is capped.
        """
        scored = []
        for alert in alerts:
            duration = alert["duration_windows"]

            # Normalize each component
            speed_norm = min(1.0, alert["total_speed_spikes"] / (duration * 8))
            fuel_norm = min(1.0, alert["max_fuel_consumption"] / self._fuel_drop_rate)
            thermal_norm = min(1.0, alert["max_thermal_deviation"] / 20.0)

            # Weighted combination
            total_weight = 0.0
            severity = 0.0
            for idx, component in enumerate([speed_norm, fuel_norm, thermal_norm]):
                weight = self._weights[idx]
                severity += component * weight
                total_weight = weight

            severity = severity / total_weight if total_weight > 0 else 0.0
            severity = min(severity, self._severity_cap)

            alert_scored = dict(alert)
            alert_scored["severity"] = round(severity, 4)
            scored.append(alert_scored)

        return scored
