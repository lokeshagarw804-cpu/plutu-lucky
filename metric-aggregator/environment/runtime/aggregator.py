"""Metric aggregator — computes windowed statistics over aligned metrics.

Applies a sliding window with configurable step to compute per-window
aggregate values (mean, max, min) for each metric of each node.
The aggregated windows are used downstream for ranking and detection.
"""
import configparser


class MetricAggregator:
    """Computes windowed aggregate statistics for node metrics."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_size = self._config.getint("aggregation", "window_size")
        self._step_size = self._config.getint("aggregation", "step_size")

    def aggregate(self, filtered_nodes):
        """Compute per-window aggregates for each node.

        For each node and metric, slides a window and computes:
        - mean: average value in window
        - max: maximum value in window
        - p90: 90th percentile approximation (sorted index method)

        Returns dict mapping node_id to list of window aggregates.
        """
        results = {}

        for node_id, node in filtered_nodes.items():
            windows = []
            metrics = node["metrics"]
            n_samples = len(metrics["latency_ms"])

            pos = 0
            window_idx = 0
            while pos + self._window_size < n_samples:
                window_agg = {"window_idx": window_idx}

                for metric_name, values in metrics.items():
                    window_vals = values[pos:pos + self._window_size]
                    window_agg[f"{metric_name}_mean"] = sum(window_vals) / len(window_vals)
                    window_agg[f"{metric_name}_max"] = max(window_vals)
                    # P90 using sorted index
                    sorted_vals = sorted(window_vals)
                    p90_idx = int(0.9 * (len(sorted_vals) - 1))
                    window_agg[f"{metric_name}_p90"] = sorted_vals[p90_idx]

                windows.append(window_agg)
                window_idx += 1
                pos += self._step_size

            results[node_id] = windows

        return results
