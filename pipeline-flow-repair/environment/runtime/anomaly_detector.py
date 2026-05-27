"""Anomaly detector — identifies pressure and flow deviations.

Compares expected vs actual pressure drops and flags sustained periods
where the relative deviation exceeds the configured threshold. Also
detects abnormal flow rate deviations from segment averages.

An anomaly event requires min_consecutive_readings consecutive
anomalous readings to reduce false positives from sensor noise.
"""
import configparser


class AnomalyDetector:
    """Detects anomalous pressure and flow readings in pipeline segments."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._pressure_threshold = self._config.getfloat(
            "anomaly", "pressure_threshold"
        )
        self._flow_threshold = self._config.getfloat(
            "anomaly", "flow_deviation_threshold"
        )
        self._min_consecutive = self._config.getint(
            "anomaly", "min_consecutive_readings"
        )

    def detect_pressure_anomalies(self, expected_drops, actual_drops):
        """Find sustained pressure deviations exceeding threshold.

        Returns dict mapping segment_id to list of anomaly records with
        reading_index, expected, actual, and deviation fields.
        """
        anomalies = {}
        for seg_id in expected_drops:
            expected = expected_drops[seg_id]
            actual = actual_drops[seg_id]
            seg_anomalies = []

            consecutive_count = 0
            for i in range(len(expected)):
                if expected[i] == 0:
                    consecutive_count = 0
                    continue
                deviation = abs(actual[i] - expected[i]) / abs(expected[i])
                if deviation >= self._pressure_threshold:
                    consecutive_count += 1
                    if consecutive_count > self._min_consecutive:
                        seg_anomalies.append({
                            "reading_index": i,
                            "expected": round(expected[i], 6),
                            "actual": round(actual[i], 6),
                            "deviation": round(deviation, 6),
                        })
                else:
                    consecutive_count = 0

            anomalies[seg_id] = seg_anomalies
        return anomalies

    def detect_flow_anomalies(self, segments, flow_stats):
        """Find sustained flow deviations from segment average."""
        anomalies = {}
        for seg_id, data in segments.items():
            readings = data["flow_readings"]
            avg_flow = flow_stats[seg_id]["avg_flow"]
            seg_anomalies = []

            if avg_flow == 0:
                anomalies[seg_id] = []
                continue

            consecutive_count = 0
            for i, flow in enumerate(readings):
                deviation = abs(flow - avg_flow) / avg_flow
                if deviation > self._flow_threshold:
                    consecutive_count += 1
                    if consecutive_count >= self._min_consecutive:
                        seg_anomalies.append({
                            "reading_index": i,
                            "flow": flow,
                            "avg_flow": avg_flow,
                            "deviation": round(deviation, 6),
                        })
                else:
                    consecutive_count = 0

            anomalies[seg_id] = seg_anomalies
        return anomalies
