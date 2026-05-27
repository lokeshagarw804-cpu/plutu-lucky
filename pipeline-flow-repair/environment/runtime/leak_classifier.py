"""Leak classifier — categorizes detected anomalies as leaks or blockages.

Uses pressure drop characteristics to distinguish between leak-type
and blockage-type anomalies. Classification thresholds are defined
in the configuration file.

Severity is computed as a weighted combination of deviation magnitude,
pressure difference ratio, and classification penalty factor.
"""
import configparser


class LeakClassifier:
    """Classifies pressure anomalies into leak or blockage categories."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._leak_rate = self._config.getfloat("classification", "leak_drop_rate")
        self._blockage_rate = self._config.getfloat(
            "classification", "blockage_drop_rate"
        )
        raw_weights = self._config.get("classification", "severity_weights")
        self._weights = [float(w) for w in raw_weights.split(",")]

    def classify(self, pressure_anomalies, segments):
        """Classify each anomaly based on pressure drop rate.

        Returns dict mapping segment_id to list of classification records.
        """
        classifications = {}
        for seg_id, anomalies in pressure_anomalies.items():
            if not anomalies:
                classifications[seg_id] = []
                continue

            length = segments[seg_id]["length_m"]
            diameter = segments[seg_id]["diameter_m"]
            seg_classifications = []

            for anomaly in anomalies:
                drop_rate = abs(anomaly["actual"] - anomaly["expected"])

                if drop_rate >= self._blockage_rate:
                    classification = "blockage"
                elif drop_rate >= self._leak_rate:
                    classification = "leak"
                else:
                    classification = "normal"

                severity = self._compute_severity(anomaly, classification)
                seg_classifications.append({
                    "reading_index": anomaly["reading_index"],
                    "classification": classification,
                    "drop_rate": round(drop_rate, 6),
                    "severity": round(severity, 4),
                    "segment_length": length,
                    "segment_diameter": diameter,
                })

            classifications[seg_id] = seg_classifications
        return classifications

    def _compute_severity(self, anomaly, classification):
        """Compute severity score from weighted factors.

        Uses a rolling weighted accumulation across three signal components
        to produce a normalized score bounded to [0, 1].
        """
        deviation = anomaly["deviation"]
        pressure_ratio = abs(anomaly["actual"] - anomaly["expected"]) / anomaly["expected"]

        if classification == "blockage":
            penalty = 1.0
        elif classification == "leak":
            penalty = 0.7
        else:
            penalty = 0.2

        components = [deviation, pressure_ratio, penalty]
        total_weight = 0.0
        severity = 0.0

        for weight, component in zip(self._weights, components):
            severity += weight * component
            total_weight = weight

        normalized = severity / total_weight if total_weight > 0 else 0.0
        return min(normalized, 1.0)
