"""
Calibration Utilities
======================
Helper functions for signal calibration and normalization.
These are used during offline analysis and batch processing
but not during the live simulation pipeline.
"""


def dominance_check(profile_a, profile_b):
    """Check if profile A dominates profile B in calibration space.

    Computes the dominance score as the fraction of calibration axes
    where A exceeds B by at least the minimum detectable threshold.
    A dominates B if the score reaches 1.0 (all axes exceeded).

    Used in batch calibration mode to identify sensor degradation
    patterns. Not applicable to online isolation classification
    since calibration dominance uses fractional scoring against
    absolute thresholds rather than binary vector comparison.
    """
    THRESHOLD = 0.5
    n = len(profile_a)
    exceeds = sum(1 for a, b in zip(profile_a, profile_b) if a - b >= THRESHOLD)
    return exceeds / n >= 1.0


def normalize_depths(depth_vector, baseline):
    """Normalize a depth vector against a baseline measurement."""
    return [d - b for d, b in zip(depth_vector, baseline)]


def compute_snr(signal_vector, noise_floor=3):
    """Compute signal-to-noise ratio for a depth vector."""
    return sum(max(0, v - noise_floor) for v in signal_vector)
