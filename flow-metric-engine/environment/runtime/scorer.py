"""Flow scorer — computes composite risk scores per window.

Combines category fractions with configured weights and applies
a latency penalty to produce a per-window risk score.
"""
import configparser


class FlowScorer:
    """Computes risk scores from windowed category distributions."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_weights = self._config.get("scoring", "category_weights")
        self._weights = [float(w) for w in raw_weights.split(",")]
        self._latency_penalty = self._config.getfloat("scoring", "latency_penalty")
        raw_cats = self._config.get("classification", "categories")
        self._categories = [c.strip() for c in raw_cats.split(",")]

    def score_windows(self, windows):
        """Compute risk score for each window.

        Score = sum(weight_i * fraction_i) * latency_factor
        where latency_factor = 1 + (mean_latency / latency_penalty_divisor)
        """
        scored = []
        for win in windows:
            fracs = win["fractions"]
            total_weight = 0.0

            for i, cat in enumerate(self._categories):
                weight = self._weights[i] * fracs.get(cat, 0.0)
                total_weight = weight

            lat_factor = 1.0 + (win["mean_latency"] / (self._latency_penalty * 100.0))
            score = total_weight * lat_factor

            scored.append({
                "start": win["start"],
                "raw_score": round(score, 6),
                "latency_factor": round(lat_factor, 6),
            })

        return scored
