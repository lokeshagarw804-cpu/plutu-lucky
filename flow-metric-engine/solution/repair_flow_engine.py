#!/usr/bin/env python3
"""Repair script for flow metric engine."""
import sys


def patch_bandwidth():
    """Fix bandwidth calculation: divide by seconds not milliseconds."""
    path = "/app/runtime/bandwidth.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug E: convert ms to seconds before dividing
    content = content.replace(
        "bandwidth_bps = total_bytes / duration_ms",
        "bandwidth_bps = total_bytes / (duration_ms / 1000.0)"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_latency():
    """Fix jitter computation to use mean absolute consecutive difference."""
    path = "/app/runtime/latency.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug B: replace variance-based jitter with consecutive diff
    old_jitter = '''        mean_lat = sum(latencies) / n
        variance = sum((lat - mean_lat) ** 2 for lat in latencies) / (n - 1)
        return math.sqrt(variance)'''

    new_jitter = '''        total_diff = sum(abs(latencies[i+1] - latencies[i]) for i in range(n-1))
        return total_diff / (n - 1)'''

    content = content.replace(old_jitter, new_jitter)

    with open(path, "w") as f:
        f.write(content)


def patch_matrix():
    """Fix interface sorting to use natural numeric order."""
    path = "/app/runtime/matrix.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug C: sort by numeric suffix
    content = content.replace(
        "interface_ids = sorted(interfaces.keys())",
        "interface_ids = sorted(interfaces.keys(), key=lambda s: int(''.join(c for c in s if c.isdigit())))"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_anomaly():
    """Fix anomaly scoring formula: weighted sum not product."""
    path = "/app/runtime/anomaly.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug D: replace product formula with correct weighted sum
    content = content.replace(
        "score = w0 * (norm_bw + w1) * (norm_p95 + w2) * norm_jit",
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
