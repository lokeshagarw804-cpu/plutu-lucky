"""Severity classifier — assigns severity tiers to fused anomaly scores.

Maps fused scores to severity tiers based on configured thresholds.
Only windows classified as warning or above are emitted as anomalies.
"""
import configparser


class SeverityClassifier:
    """Classifies fused anomaly scores into severity tiers."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._warning = self._config.getfloat("scoring", "z_threshold_warning")
        self._critical = self._config.getfloat("scoring", "z_threshold_critical")
        self._emergency = self._config.getfloat("scoring", "z_threshold_emergency")

    def classify(self, fused_windows):
        """Classify each fused window into a severity tier.

        Args:
            fused_windows: list of dicts from SensorFusion

        Returns:
            list of anomaly dicts (only warning+ severity included)
        """
        anomalies = []

        for w in fused_windows:
            score = w["fused_score"]
            severity = self._determine_severity(score)
            if severity != "normal":
                anomalies.append({
                    "window_start": w["window_start"],
                    "window_end": w["window_end"],
                    "fused_score": w["fused_score"],
                    "severity": severity,
                    "sensors_reporting": w["sensors_reporting"],
                })

        return anomalies

    def _determine_severity(self, score):
        """Map score to severity tier using threshold cascade."""
        if score >= self._warning:
            return "warning"
        elif score >= self._critical:
            return "critical"
        elif score >= self._emergency:
            return "emergency"
        return "normal"
