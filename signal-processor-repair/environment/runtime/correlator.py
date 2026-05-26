"""
Cross-station correlation engine.

Computes pairwise correlation coefficients between station signals
within sliding time windows. Correlation values represent the
statistical relationship between readings from different stations
on the same channel within each window.

Valid Pearson correlation coefficients are bounded in [-1.0, 1.0].
Each window produces independent correlation measurements that should
not carry state from previous windows.
"""

import configparser
from collections import defaultdict


class Correlator:
    """Computes cross-station signal correlations."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._method = config.get("correlation", "method")
        self._min_pairs = config.getint("correlation", "min_pair_readings")
        self._significance = config.getfloat("correlation", "significance_level")
        self._correlation_sums = defaultdict(float)
        self._window_count = defaultdict(int)

    def compute_correlations(self, calibrated_readings, windows):
        """Compute pairwise correlations across windows.

        For each window, groups readings by station and channel,
        then computes Pearson correlation between all station pairs
        that have sufficient overlapping readings.
        """
        pair_results = []

        for window in windows:
            window_readings = self._get_window_readings(
                calibrated_readings, window
            )
            pairs = self._compute_window_correlations(window_readings)
            pair_results.extend(pairs)

        return self._build_correlation_matrix(pair_results)

    def _get_window_readings(self, readings, window):
        """Get readings that fall within the time window."""
        start, end = window
        return [
            r for r in readings
            if start <= r["timestamp"] <= end
        ]

    def _compute_window_correlations(self, window_readings):
        """Compute correlations for all station pairs in a window."""
        by_station_channel = defaultdict(list)
        for r in window_readings:
            key = (r["station_id"], r["channel"])
            by_station_channel[key].append(r["calibrated_value"])

        pairs = []
        stations = sorted(set(r["station_id"] for r in window_readings))
        channels = sorted(set(r["channel"] for r in window_readings))

        for channel in channels:
            for i, s1 in enumerate(stations):
                for s2 in stations[i + 1:]:
                    vals1 = by_station_channel.get((s1, channel), [])
                    vals2 = by_station_channel.get((s2, channel), [])

                    min_len = min(len(vals1), len(vals2))
                    if min_len < self._min_pairs:
                        continue

                    v1 = vals1[:min_len]
                    v2 = vals2[:min_len]
                    corr = self._pearson(v1, v2)

                    if corr is not None:
                        pair_key = f"{s1}:{s2}:{channel}"
                        self._correlation_sums[pair_key] += corr
                        self._window_count[pair_key] += 1
                        pairs.append({
                            "station_a": s1,
                            "station_b": s2,
                            "channel": channel,
                            "correlation": corr,
                        })

        return pairs

    def _pearson(self, x, y):
        """Compute Pearson correlation coefficient."""
        n = len(x)
        if n < 2:
            return None

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        den_x = sum((xi - mean_x) ** 2 for xi in x) ** 0.5
        den_y = sum((yi - mean_y) ** 2 for yi in y) ** 0.5

        if den_x == 0 or den_y == 0:
            return None

        return round(num / (den_x * den_y), 6)

    def _build_correlation_matrix(self, pair_results):
        """Build the final correlation matrix from pair results.

        Uses averaged correlations across windows for each pair.
        """
        matrix = {}
        for pair_key, total in self._correlation_sums.items():
            count = self._window_count[pair_key]
            matrix[pair_key] = {
                "pair": pair_key,
                "avg_correlation": round(total, 6),
                "window_count": count,
                "total_correlation": round(total, 6),
            }
        return matrix
