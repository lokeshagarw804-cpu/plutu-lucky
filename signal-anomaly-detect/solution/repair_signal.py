"""Repair script for signal anomaly detection pipeline.

Fixes four interacting bugs:
1. spectrum.py — DFT magnitude uses only real component (missing imag²)
2. detector.py — Variance divides by N (population) instead of N-1 (sample)
3. smoother.py — Overlapping windows keep first score instead of maximum
4. detector.py — Reads threshold from wrong config section
"""


def patch_file(path, old, new):
    with open(path, "r") as f:
        content = f.read()
    if old not in content:
        raise RuntimeError(f"Patch target not found in {path}:\n  {repr(old)}")
    content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)


# Bug 1: spectrum.py — magnitude formula missing imaginary component
# sqrt(real_part ** 2) should be sqrt(real_part ** 2 + imag_part ** 2)
patch_file(
    "/app/runtime/spectrum.py",
    "magnitude = math.sqrt(real_part ** 2) / N",
    "magnitude = math.sqrt(real_part ** 2 + imag_part ** 2) / N",
)

# Bug 2: detector.py — variance uses population formula (/ N) instead of sample (/ N-1)
patch_file(
    "/app/runtime/detector.py",
    "variance = sum((x - mean) ** 2 for x in values) / len(values)",
    "variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)",
)

# Bug 3: smoother.py — overlapping windows take first instead of max
patch_file(
    "/app/runtime/smoother.py",
    "                    if ts not in smoothed_scores:\n                        smoothed_scores[ts] = score",
    "                    if ts not in smoothed_scores or score > smoothed_scores[ts]:\n                        smoothed_scores[ts] = score",
)

# Bug 4: detector.py — threshold from [detection] (2.0) instead of [detection.tuned] (1.5)
patch_file(
    "/app/runtime/detector.py",
    'self._threshold = self._config.getfloat("detection", "threshold")',
    'self._threshold = self._config.getfloat("detection.tuned", "threshold")',
)

print("All patches applied successfully.")
