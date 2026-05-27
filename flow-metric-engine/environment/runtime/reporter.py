"""Violation reporter — identifies threshold violations and summarizes.

Analyzes scored windows to find violations exceeding the configured
threshold, then builds a per-flow and aggregate report.
"""
import configparser


class ViolationReporter:
    """Detects and reports threshold violations from scored windows."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._threshold = self._config.getfloat("scoring", "violation_threshold")
        self._window_size = self._config.getint("classification", "window_size")

    def report(self, flow_scores):
        """Build violation report across all flows.

        For each flow, identifies windows exceeding the threshold,
        computes the violation ratio (violating windows / total windows),
        and determines the peak score.

        flow_scores: dict of flow_id -> list of scored window records
        """
        flow_reports = []
        total_violations = 0
        total_windows = 0

        for flow_id in sorted(flow_scores.keys()):
            scored = flow_scores[flow_id]
            n_windows = len(scored)
            total_windows += n_windows

            violations = []
            for win in scored:
                if win["raw_score"] > self._threshold:
                    violations.append(win)
                    total_violations += 1

            n_violations = len(violations)
            peak_score = max((w["raw_score"] for w in scored), default=0.0)
            avg_score = sum(w["raw_score"] for w in scored) / n_windows if n_windows > 0 else 0.0

            # Violation density: violations per expected window count
            # BUG 4: uses packet_count // window_size as denominator
            # instead of actual n_windows
            expected_windows = 150 // self._window_size  # hardcoded packet count
            violation_ratio = n_violations / expected_windows if expected_windows > 0 else 0.0

            flow_reports.append({
                "flow_id": flow_id,
                "total_windows": n_windows,
                "violations": n_violations,
                "violation_ratio": round(violation_ratio, 6),
                "peak_score": round(peak_score, 6),
                "avg_score": round(avg_score, 6),
            })

        # Sort by peak_score descending
        flow_reports.sort(key=lambda r: r["peak_score"], reverse=True)

        return {
            "threshold": self._threshold,
            "total_flows": len(flow_reports),
            "total_windows_analyzed": total_windows,
            "total_violations": total_violations,
            "flows": flow_reports,
        }
