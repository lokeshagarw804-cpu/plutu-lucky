"""Causality checker — detects happens-before violations using vector clocks.

Compares vector clock values between events to identify causal ordering
violations where an event appears to depend on a future event from
another node (impossible in correct causal ordering).
"""
import configparser


class CausalityChecker:
    """Detects causal ordering violations in distributed event streams."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._max_drift = self._config.getint("causality", "max_drift_ms")

    def detect_violations(self, events):
        """Find all happens-before violations in the event stream.

        A violation occurs when event B has a vector clock that
        indicates it happened-before event A, but B's timestamp
        is AFTER A's timestamp (within the max drift tolerance).

        Two events are concurrent if neither's clock dominates.
        A dominates B if A[i] >= B[i] for all i and A[j] > B[j] for some j.
        """
        violations = []
        # Compare events within same window
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
                        # B should have come before A but A appears first
                        time_diff = ev_b["ts_ms"] - ev_a["ts_ms"]
                        if abs(time_diff) <= self._max_drift:
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
        """Compare two vector clocks to determine causal relationship.

        Returns:
            'a_before_b' if A happens-before B
            'b_before_a' if B happens-before A
            'concurrent' if neither dominates
        """
        all_nodes = set(list(clock_a.keys()) + list(clock_b.keys()))

        a_dominates = True
        b_dominates = True
        a_has_greater = False
        b_has_greater = False

        for node in all_nodes:
            val_a = clock_a.get(node, 0)
            val_b = clock_b.get(node, 0)

            if val_a > val_b:
                b_dominates = False
                a_has_greater = True
            elif val_b > val_a:
                a_dominates = False
                b_has_greater = True

        if a_dominates and a_has_greater:
            return "a_before_b"
        if b_dominates and b_has_greater:
            return "b_before_a"

        # Both have some greater values — should be concurrent
        # but we check if clocks are actually equal
        if not a_has_greater and not b_has_greater:
            return "concurrent"

        return "a_before_b"
