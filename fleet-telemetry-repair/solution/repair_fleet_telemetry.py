#!/usr/bin/env python3
"""Repair script for fleet telemetry anomaly detection pipeline."""
import sys


def patch_scorer():
    """Fix EWMA update: decay weight and diff computation order."""
    path = "/app/runtime/scorer.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix warmup branch: move diff after mean update, fix alpha*old -> (1-alpha)*old
    old_warmup = (
        "                    diff = value - ewma_mean\n"
        "                    ewma_mean = self._alpha * value + self._alpha * ewma_mean\n"
        "                    ewma_var = self._alpha * (diff ** 2) + self._alpha * ewma_var"
    )
    new_warmup = (
        "                    ewma_mean = self._alpha * value + (1 - self._alpha) * ewma_mean\n"
        "                    diff = value - ewma_mean\n"
        "                    ewma_var = self._alpha * (diff ** 2) + (1 - self._alpha) * ewma_var"
    )
    content = content.replace(old_warmup, new_warmup)

    # Fix post-warmup branch: move diff after mean update, fix alpha*old -> (1-alpha)*old
    old_main = (
        "                diff = value - ewma_mean\n"
        "                ewma_mean = self._alpha * value + self._alpha * ewma_mean\n"
        "                ewma_var = self._alpha * (diff ** 2) + self._alpha * ewma_var"
    )
    new_main = (
        "                ewma_mean = self._alpha * value + (1 - self._alpha) * ewma_mean\n"
        "                diff = value - ewma_mean\n"
        "                ewma_var = self._alpha * (diff ** 2) + (1 - self._alpha) * ewma_var"
    )
    content = content.replace(old_main, new_main)

    with open(path, "w") as f:
        f.write(content)


def patch_aggregator():
    """Fix window boundary comparison from strict to inclusive."""
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()

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
    """Fix weighted average divisor and window_end computation."""
    path = "/app/runtime/fusion.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix divisor: use sum of weights instead of sensor count
    old_block = '''            for sensor, w in sensor_data.items():
                weight = self._weights.get(sensor, 1.0)
                total_score += weight * w["peak_z"]
                n_sensors += 1

            # Compute weighted average
            fused_score = total_score / n_sensors if n_sensors > 0 else 0.0'''

    new_block = '''            total_weight = 0.0
            for sensor, w in sensor_data.items():
                weight = self._weights.get(sensor, 1.0)
                total_score += weight * w["peak_z"]
                total_weight += weight
                n_sensors += 1

            # Compute weighted average
            fused_score = total_score / total_weight if total_weight > 0 else 0.0'''

    content = content.replace(old_block, new_block)

    # Fix window_end: use self._window_size instead of hardcoded 5
    content = content.replace(
        '"window_end": start + 5,',
        '"window_end": start + self._window_size,'
    )

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
