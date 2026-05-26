"""Sliding-window smoothing with overlap handling."""
import configparser
from typing import List, Dict, Any


class WindowSmoother:
    """Applies sliding window smoothing across station readings."""

    def __init__(self, config_path: str):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_size = self._config.getint("smoothing", "window_size")
        self._overlap = self._config.getint("smoothing", "overlap")

    def _smooth_window(self, values: List[float]) -> float:
        """Compute smoothed value for a single window."""
        if not values:
            return 0.0
        weights = list(range(1, len(values) + 1))
        total_weight = sum(weights)
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        return weighted_sum / total_weight

    def apply(self, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply sliding window smoothing per station."""
        stations = {}
        for r in readings:
            stations.setdefault(r["station"], []).append(r)

        results = []
        for station, records in sorted(stations.items()):
            values = [r["value"] for r in records]
            timestamps = [r["ts_ms"] for r in records]

            smoothed_scores = {}
            step = self._window_size - self._overlap

            for start in range(0, len(values), step):
                end = min(start + self._window_size, len(values))
                window_vals = values[start:end]
                if len(window_vals) < 2:
                    continue

                score = self._smooth_window(window_vals)

                for idx in range(start, end):
                    ts = timestamps[idx]
                    if ts not in smoothed_scores:
                        smoothed_scores[ts] = score

            for ts in sorted(smoothed_scores.keys()):
                results.append({
                    "station": station,
                    "ts_ms": ts,
                    "smoothed_value": smoothed_scores[ts],
                })

        return results
