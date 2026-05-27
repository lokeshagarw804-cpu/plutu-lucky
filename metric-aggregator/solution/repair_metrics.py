#!/usr/bin/env python3
"""Repair script for metric aggregation engine."""
import sys


def patch_aggregator():
    """Fix window boundary off-by-one in aggregator."""
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug #4: window boundary — < should be <=
    # The condition `pos + window_size < n_samples` skips the last valid window
    content = content.replace(
        "while pos + self._window_size < n_samples:",
        "while pos + self._window_size <= n_samples:"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_ranker():
    """Fix weight accumulator and remove exclude_node filter."""
    path = "/app/runtime/ranker.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug #3: remove exclude_node filter — all nodes must participate in ranking
    content = content.replace(
        """        # Filter out infrastructure nodes from ranking comparison
        ranked_nodes = {
            nid: windows for nid, windows in aggregated.items()
            if nid != self._exclude_node
        }""",
        """        ranked_nodes = {
            nid: windows for nid, windows in aggregated.items()
        }"""
    )

    # Fix Bug #2: weight accumulator — second line should use += not =
    content = content.replace(
        "raw_score = self._weight_latency * norm_lat\n                raw_score = self._weight_error * norm_err",
        "raw_score = self._weight_latency * norm_lat\n                raw_score += self._weight_error * norm_err"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_detector():
    """Fix threshold comparison to include boundary value."""
    path = "/app/runtime/detector.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug #1: threshold comparison — should use >= not >
    content = content.replace(
        "if pct > self._threshold:",
        "if pct >= self._threshold:"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_aggregator()
    patch_ranker()
    patch_detector()

    # Re-run the pipeline with fixes applied
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.main import main as run_main
    run_main()


if __name__ == "__main__":
    main()
