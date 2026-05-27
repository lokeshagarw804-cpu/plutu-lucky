#!/usr/bin/env python3
"""Repair script for fleet telemetry anomaly detection pipeline."""
import sys


def patch_scorer():
    """Fix EWMA decay weight in mean and variance updates."""
    path = "/app/runtime/scorer.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug 1a: warmup mean update uses alpha*old instead of (1-alpha)*old
    content = content.replace(
        "ewma_mean = self._alpha * value + self._alpha * ewma_mean\n"
        "                    diff = value - ewma_mean\n"
        "                    ewma_var = self._alpha * (diff ** 2) + self._alpha * ewma_var",
        "ewma_mean = self._alpha * value + (1 - self._alpha) * ewma_mean\n"
        "                    diff = value - ewma_mean\n"
        "                    ewma_var = self._alpha * (diff ** 2) + (1 - self._alpha) * ewma_var"
    )

    # Fix Bug 1b: post-warmup mean/var update uses alpha*old instead of (1-alpha)*old
    content = content.replace(
        "ewma_mean = self._alpha * value + self._alpha * ewma_mean\n"
        "                diff = value - ewma_mean\n"
        "                ewma_var = self._alpha * (diff ** 2) + self._alpha * ewma_var",
        "ewma_mean = self._alpha * value + (1 - self._alpha) * ewma_mean\n"
        "                diff = value - ewma_mean\n"
        "                ewma_var = self._alpha * (diff ** 2) + (1 - self._alpha) * ewma_var"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_aggregator():
    """Fix window boundary comparison from strict to inclusive."""
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug 2: use >= instead of > for window boundary
    content = content.replace(
        "while ts - current_start > self._window_size:",
        "while ts - current_start >= self._window_size:"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_classifier():
    """Fix severity threshold cascade to check highest first."""
    path = "/app/runtime/classifier.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug 3: check thresholds from highest to lowest
    old_method = '''    def _determine_severity(self, score):
        """Map score to severity tier using threshold cascade."""
        if score >= self._warning:
            return "warning"
        elif score >= self._critical:
            return "critical"
        elif score >= self._emergency:
            return "emergency"
        return "normal"'''

    new_method = '''    def _determine_severity(self, score):
        """Map score to severity tier using threshold cascade."""
        if score >= self._emergency:
            return "emergency"
        elif score >= self._critical:
            return "critical"
        elif score >= self._warning:
            return "warning"
        return "normal"'''

    content = content.replace(old_method, new_method)

    with open(path, "w") as f:
        f.write(content)


def patch_fusion():
    """Fix weighted average to divide by sum of weights, not sensor count."""
    path = "/app/runtime/fusion.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug 4: track total_weight instead of dividing by n_sensors
    old_block = '''            for sensor, w in sensor_data.items():
                weight = self._weights.get(sensor, 1.0)
                total_score += weight * w["peak_z"]
                n_sensors += 1

            # Compute weighted average — divide by sensor count
            fused_score = total_score / n_sensors if n_sensors > 0 else 0.0'''

    new_block = '''            total_weight = 0.0
            for sensor, w in sensor_data.items():
                weight = self._weights.get(sensor, 1.0)
                total_score += weight * w["peak_z"]
                total_weight += weight
                n_sensors += 1

            # Compute weighted average — divide by sum of weights
            fused_score = total_score / total_weight if total_weight > 0 else 0.0'''

    content = content.replace(old_block, new_block)

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_scorer()
    patch_aggregator()
    patch_classifier()
    patch_fusion()

    # Re-run the pipeline with fixes applied
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.main import main as run_main
    run_main()


if __name__ == "__main__":
    main()
