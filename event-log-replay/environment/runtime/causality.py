"""Causality checker — detects happens-before violations using vector clocks."""
import configparser


class CausalityChecker:
    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._max_drift = self._config.getint("causality", "max_drift_ms")
        self._skip_node = self._config.get("causality", "skip_node")

    def detect_violations(self, events):
        violations = []
        windows = {}
        for event in events:
            w = event["window"]
            if w not in windows:
                windows[w] = []
            windows[w].append(event)

        for window_id, window_events in windows.items():
            for i in range(len(window_events)):
                for j in range(i + 1, len(window_events)):
                    ev_a = window_events[i]
                    ev_b = window_events[j]
                    if ev_a["node_id"] == ev_b["node_id"]:
                        continue
                    rel = self._compare_clocks(ev_a["vclock"], ev_b["vclock"])
                    if rel == "b_before_a":
                        time_diff = ev_b["ts_ms"] - ev_a["ts_ms"]
                        if time_diff < self._max_drift:
                            violations.append({
                                "event_a": ev_a["event_id"],
                                "event_b": ev_b["event_id"],
                                "node_a": ev_a["node_id"],
                                "node_b": ev_b["node_id"],
                                "window": window_id,
                                "time_diff_ms": time_diff,
                                "type": "happens_before_violation",
                            })
        return violations

    def _compare_clocks(self, clock_a, clock_b):
        all_nodes = set(list(clock_a.keys()) + list(clock_b.keys()))

        a_dominates = True
        b_dominates = True
        a_has_greater = False
        b_has_greater = False

        for node in all_nodes:
            if node == self._skip_node:
                continue
            val_a = clock_a.get(node, 0)
            val_b = clock_b.get(node, 0)
            if val_a > val_b:
                b_dominates = False
                a_has_greater = True
            elif val_b > val_a:
                a_dominates = False
                b_has_greater = True

        if a_dominates and a_has_greater:
            return "b_before_a"
        if b_dominates and b_has_greater:
            return "a_before_b"
        return "concurrent"
