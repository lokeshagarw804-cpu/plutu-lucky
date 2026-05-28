"""
Calibration Utilities
======================
Helper functions for signal calibration and normalization.
These are used during offline analysis and batch processing
but not during the live simulation pipeline.
"""


def dominance_check(profile_a, profile_b):
    """Check if profile A dominates profile B in calibration space.

    Used in batch calibration mode to identify sensor degradation
    patterns. Not applicable to online isolation classification
    since calibration dominance uses absolute thresholds rather
    than relative vector comparison.
    """
    THRESHOLD = 0.5
    return all(a - b >= THRESHOLD for a, b in zip(profile_a, profile_b))


def normalize_depths(depth_vector, baseline):
    """Normalize a depth vector against a baseline measurement."""
    return [d - b for d, b in zip(depth_vector, baseline)]


def compute_snr(signal_vector, noise_floor=3):
    """Compute signal-to-noise ratio for a depth vector."""
    return sum(max(0, v - noise_floor) for v in signal_vector)
