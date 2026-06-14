"""Anomaly reporter — generates severity-ranked violation reports."""
import configparser


class AnomalyReporter:
    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._min_severity = self._config.getfloat("reporting", "min_severity")
        self._weights = self._parse_weights()
        self._confidence_decay = self._config.getfloat("reporting", "confidence_decay")

    def _parse_weights(self):
        raw = self._config.get("reporting", "weights")
        return [float(w) for w in raw.split(",")]

    def generate_report(self, violations, events):
        if not violations:
            return [], {"total_anomalies": 0, "nodes_affected": 0,
                       "total_violations": 0, "max_severity": 0.0}

        node_order = sorted(set(e["node_id"] for e in events))

        by_source = {}
        for v in violations:
            src = v["node_a"]
            if src not in by_source:
                by_source[src] = []
            by_source[src].append(v)

        anomalies = []
        for source_node, node_violations in by_source.items():
            weighted_sum = 0.0
            total_weight = 0.0

            by_target = {}
            for v in node_violations:
                tgt = v["node_b"]
                if tgt not in by_target:
                    by_target[tgt] = []
                by_target[tgt].append(v)

            for target_node, target_viol in by_target.items():
                tgt_idx = node_order.index(target_node) if target_node in node_order else 0
                weight = self._weights[tgt_idx] if tgt_idx < len(self._weights) else 0.1

                count_score = min(len(target_viol) / 5.0, 1.0)
                avg_drift = sum(abs(v["time_diff_ms"]) for v in target_viol) / len(target_viol)
                drift_score = max(0, 1.0 - avg_drift / self._config.getint("causality", "max_drift_ms"))
                combined = (count_score + drift_score) / 2.0

                weighted_sum += weight * combined
                total_weight = weight

            # Apply confidence factor based on window spread
            windows_hit = set(v["window"] for v in node_violations)
            confidence = self._confidence_decay ** (4 - min(len(windows_hit), 4))

            severity = (weighted_sum / total_weight) * confidence if total_weight > 0 else 0.0

            if severity >= self._min_severity:
                anomalies.append({
                    "source_node": source_node,
                    "severity": round(severity, 4),
                    "violation_count": len(node_violations),
                    "target_nodes": sorted(by_target.keys()),
                })

        anomalies.sort(key=lambda a: (-a["severity"], a["source_node"]))

        summary = {
            "total_anomalies": len(anomalies),
            "nodes_affected": len(set(a["source_node"] for a in anomalies)),
            "total_violations": len(violations),
            "max_severity": max((a["severity"] for a in anomalies), default=0.0),
        }

        return anomalies, summary
