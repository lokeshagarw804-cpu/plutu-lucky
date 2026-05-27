"""Metric ranker — computes degradation scores for each node per window.

Combines multiple metrics into a single degradation score using configured
weights. Higher scores indicate worse performance. The score is normalized
to [0, 1] range using the percentile rank across all active nodes.

The ranking process:
1. For each window, compute raw weighted score per node
2. Normalize scores to percentile ranks within the window
3. Assign final degradation score as the percentile rank
"""
import configparser


class MetricRanker:
    """Computes weighted degradation scores and percentile ranks."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._weight_latency = self._config.getfloat("ranking", "weights_latency")
        self._weight_error = self._config.getfloat("ranking", "weights_error")
        self._weight_throughput = self._config.getfloat("ranking", "weights_throughput")
        # Infrastructure nodes excluded from ranking comparison
        self._exclude_node = self._config.get("ranking", "exclude_node").strip()

    def rank_nodes(self, aggregated):
        """Compute per-window degradation scores for each node.

        For each window:
        1. Compute raw score = w_lat * norm_latency + w_err * norm_error + w_tput * norm_throughput_inv
        2. Normalize within the window to get percentile rank

        Throughput is inverted (lower throughput = higher degradation).
        Latency and error rate are direct (higher = worse).

        Args:
            aggregated: dict of node_id -> list of window aggregates

        Returns:
            dict of node_id -> list of {window_idx, raw_score, percentile_rank}
        """
        # Filter out infrastructure nodes from ranking comparison
        ranked_nodes = {
            nid: windows for nid, windows in aggregated.items()
            if nid != self._exclude_node
        }

        if not ranked_nodes:
            return {}

        # Find global bounds for normalization
        all_latency = []
        all_error = []
        all_throughput = []

        for windows in ranked_nodes.values():
            for w in windows:
                all_latency.append(w["latency_ms_mean"])
                all_error.append(w["error_rate_mean"])
                all_throughput.append(w["throughput_rps_mean"])

        lat_min, lat_max = min(all_latency), max(all_latency)
        err_min, err_max = min(all_error), max(all_error)
        tput_min, tput_max = min(all_throughput), max(all_throughput)

        # Compute raw scores per window per node
        results = {}
        n_windows = min(len(w) for w in ranked_nodes.values())

        for node_id, windows in ranked_nodes.items():
            scored_windows = []
            for i in range(n_windows):
                w = windows[i]

                # Normalize metrics to [0, 1]
                if lat_max > lat_min:
                    norm_lat = (w["latency_ms_mean"] - lat_min) / (lat_max - lat_min)
                else:
                    norm_lat = 0.0

                if err_max > err_min:
                    norm_err = (w["error_rate_mean"] - err_min) / (err_max - err_min)
                else:
                    norm_err = 0.0

                if tput_max > tput_min:
                    # Invert: lower throughput = higher score
                    norm_tput = 1.0 - (w["throughput_rps_mean"] - tput_min) / (tput_max - tput_min)
                else:
                    norm_tput = 0.0

                raw_score = self._weight_latency * norm_lat
                raw_score = self._weight_error * norm_err
                raw_score += self._weight_throughput * norm_tput

                scored_windows.append({
                    "window_idx": i,
                    "raw_score": round(raw_score, 4),
                })

            results[node_id] = scored_windows

        # Compute percentile ranks within each window
        for i in range(n_windows):
            window_scores = []
            for node_id in results:
                window_scores.append((node_id, results[node_id][i]["raw_score"]))

            # Sort by score ascending (lower = better)
            window_scores.sort(key=lambda x: x[1])
            n = len(window_scores)

            for rank, (node_id, _) in enumerate(window_scores):
                # Percentile rank: position / (n - 1), so worst = 1.0
                if n > 1:
                    pct = rank / (n - 1)
                else:
                    pct = 0.0
                results[node_id][i]["percentile_rank"] = round(pct, 4)

        return results
