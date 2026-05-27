"""Anomaly detector — identifies abnormal traffic flows.

Computes a composite anomaly score for each interface from normalized
per-window metrics. Flags interfaces where the score exceeds the
configured threshold for a minimum number of consecutive windows.
"""
import configparser


class AnomalyDetector:
    """Detects anomalous traffic patterns from flow metrics."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_weights = self._config.get("anomaly", "score_weights")
        self._weights = [float(w) for w in raw_weights.split(",")]
        self._threshold = self._config.getfloat("anomaly", "threshold")
        self._min_consecutive = self._config.getint("anomaly", "min_consecutive")

    def detect(self, interfaces, bw_results, lat_results):
        """Detect anomalous interfaces based on composite scoring.

        Uses min-max normalization across all interfaces for each metric,
        then applies configured weights to produce a per-window score.

        Returns list of anomaly records for flagged interfaces.
        """
        # Gather global stats for normalization
        all_bw = []
        all_p95 = []
        all_jitter = []

        for iface_id in interfaces:
            bw = bw_results[iface_id]
            lat = lat_results[iface_id]
            for w in bw:
                all_bw.append(w["bandwidth_bps"])
            for w in lat:
                all_p95.append(w["percentile_value"])
                all_jitter.append(w["jitter"])

        bw_min, bw_max = min(all_bw), max(all_bw)
        p95_min, p95_max = min(all_p95), max(all_p95)
        jit_min, jit_max = min(all_jitter), max(all_jitter)

        bw_range = bw_max - bw_min if bw_max != bw_min else 1.0
        p95_range = p95_max - p95_min if p95_max != p95_min else 1.0
        jit_range = jit_max - jit_min if jit_max != jit_min else 1.0

        w0, w1, w2 = self._weights

        anomalies = []
        for iface_id in interfaces:
            bw = bw_results[iface_id]
            lat = lat_results[iface_id]

            # Compute per-window scores
            n_windows = min(len(bw), len(lat))
            scores = []
            for idx in range(n_windows):
                norm_bw = (bw[idx]["bandwidth_bps"] - bw_min) / bw_range
                norm_p95 = (lat[idx]["percentile_value"] - p95_min) / p95_range
                norm_jit = (lat[idx]["jitter"] - jit_min) / jit_range

                score = w0 * norm_bw + w2 * norm_p95 + w1 * norm_jit

                scores.append(round(score, 6))

            # Find consecutive windows exceeding threshold
            runs = self._find_runs(scores)

            if runs:
                max_score = max(scores)
                avg_score = sum(scores) / len(scores) if scores else 0
                anomalies.append({
                    "interface_id": iface_id,
                    "max_score": round(max_score, 6),
                    "avg_score": round(avg_score, 6),
                    "flagged_runs": len(runs),
                    "total_flagged_windows": sum(r["length"] for r in runs),
                    "runs": runs,
                })

        # Sort anomalies by max_score descending
        anomalies.sort(key=lambda a: a["max_score"], reverse=True)
        return anomalies

    def _find_runs(self, scores):
        """Find consecutive runs of scores exceeding the threshold."""
        runs = []
        run_start = None
        run_length = 0

        for idx, score in enumerate(scores):
            if score > self._threshold:
                if run_start is None:
                    run_start = idx
                run_length += 1
            else:
                if run_length >= self._min_consecutive:
                    runs.append({
                        "start_window": run_start,
                        "end_window": run_start + run_length - 1,
                        "length": run_length,
                    })
                run_start = None
                run_length = 0

        # Check final run
        if run_length >= self._min_consecutive:
            runs.append({
                "start_window": run_start,
                "end_window": run_start + run_length - 1,
                "length": run_length,
            })

        return runs
