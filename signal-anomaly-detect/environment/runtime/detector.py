"""Anomaly detection using statistical threshold scoring."""
import configparser
import math
from typing import List, Dict, Any, Tuple


class AnomalyDetector:
    """Detects anomalies based on frequency magnitude scoring."""

    def __init__(self, config_path: str):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._threshold = self._config.getfloat("detection", "threshold")
        self._min_score = self._config.getfloat("detection", "min_score")

    def _compute_zscore(self, values: List[float], target: float) -> float:
        """Compute z-score of target relative to value distribution."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)

        if variance < 1e-10:
            return 0.0

        std_dev = math.sqrt(variance)
        return abs(target - mean) / std_dev

    def detect(
        self, features: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Run anomaly detection across all frequency features."""
        anomalies = []

        for feat in features:
            magnitude = feat["magnitude"]
            values = feat["values"]
            station = feat["station"]
            band = feat["frequency_band"]

            score = self._compute_zscore(values, magnitude)

            if score >= self._threshold and magnitude >= self._min_score:
                anomalies.append({
                    "station": station,
                    "ts_ms": int(band * 1000),
                    "score": round(score, 6),
                    "frequency_band": band,
                })

        anomalies.sort(key=lambda a: (-a["score"], a["station"], a["frequency_band"]))

        stations_affected = list(set(a["station"] for a in anomalies))
        stations_affected.sort()

        summary = {
            "total_anomalies": len(anomalies),
            "stations_affected": stations_affected,
            "max_score": round(max((a["score"] for a in anomalies), default=0.0), 6),
            "avg_score": round(
                sum(a["score"] for a in anomalies) / len(anomalies)
                if anomalies
                else 0.0,
                6,
            ),
        }

        return anomalies, summary
