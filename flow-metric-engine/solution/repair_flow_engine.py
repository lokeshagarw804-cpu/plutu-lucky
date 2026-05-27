#!/usr/bin/env python3
"""Repair script for flow metric engine."""
import sys


def patch_bandwidth():
    """Fix bandwidth units: divide by seconds not milliseconds."""
    path = "/app/runtime/bandwidth.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "bandwidth_bps = total_bytes / duration_ms",
        "bandwidth_bps = total_bytes / (duration_ms / 1000.0)"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_latency():
    """Fix jitter to use mean absolute consecutive difference,
    and fix percentile rank formula off-by-one."""
    path = "/app/runtime/latency.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix jitter: replace std-dev with mean absolute consecutive diff
    old_jitter = '''        mean_lat = sum(latencies) / n
        variance = sum((lat - mean_lat) ** 2 for lat in latencies) / (n - 1)
        return math.sqrt(variance)'''

    new_jitter = '''        total_diff = sum(abs(latencies[i+1] - latencies[i]) for i in range(n-1))
        return total_diff / (n - 1)'''

    content = content.replace(old_jitter, new_jitter)

    # Fix percentile: rank should use (N-1) not N
    content = content.replace(
        "rank = (percentile / 100.0) * n",
        "rank = (percentile / 100.0) * (n - 1)"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_matrix():
    """Fix interface sorting to use natural numeric order."""
    path = "/app/runtime/matrix.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "interface_ids = sorted(interfaces.keys())",
        "interface_ids = sorted(interfaces.keys(), key=lambda s: int(''.join(c for c in s if c.isdigit())))"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_anomaly():
    """Fix weight assignment: w1 goes to p95, w2 goes to jitter."""
    path = "/app/runtime/anomaly.py"
    with open(path, "r") as f:
        content = f.read()

    # Weights are swapped: w2 applied to p95 and w1 to jitter, should be reversed
    content = content.replace(
        "score = w0 * norm_bw + w2 * norm_p95 + w1 * norm_jit",
        "score = w0 * norm_bw + w1 * norm_p95 + w2 * norm_jit"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_bandwidth()
    patch_latency()
    patch_matrix()
    patch_anomaly()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.main import main as run_main
    run_main()


if __name__ == "__main__":
    main()
