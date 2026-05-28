# PLUTU-LUCKY-CANARY
"""Frequency-domain bandpass filtering for lattice node signals.

Implements biquad IIR bandpass filters with bilinear transform
pre-warping and multi-stage cascade composition for steep rolloff.
"""

import math


def compute_biquad_coefficients(freq_low, freq_high, sampling_rate):
    """Compute biquad bandpass filter coefficients.

    Uses bilinear transform with frequency pre-warping to map the
    analog prototype to digital domain accurately.

    Args:
        freq_low: Lower cutoff frequency in Hz.
        freq_high: Upper cutoff frequency in Hz.
        sampling_rate: Sampling rate in Hz.

    Returns:
        Tuple of (b_coeffs, a_coeffs) for the biquad filter.
    """
    omega_low = 2.0 * math.pi * freq_low / sampling_rate
    omega_high = 2.0 * math.pi * freq_high / sampling_rate

    omega_low_warped = 2.0 * math.tan(omega_low / 2.0)
    omega_high_warped = 2.0 * math.tan(omega_high / 2.0)

    bw = omega_high_warped - omega_low_warped
    center = math.sqrt(omega_low_warped * omega_high_warped)

    q = center / bw
    alpha = math.sin(center) / (2.0 * q) if q > 1e-10 else 0.5

    b0 = alpha
    b1 = 0.0
    b2 = -alpha
    a0 = 1.0 + alpha
    a1 = -2.0 * math.cos(center)
    a2 = 1.0 - alpha

    b_coeffs = (b0 / a0, b1 / a0, b2 / a0)
    a_coeffs = (1.0, a1 / a0, a2 / a0)

    return b_coeffs, a_coeffs


def apply_biquad_filter(samples, b_coeffs, a_coeffs):
    """Apply a biquad filter to signal samples using Direct Form I.

    Args:
        samples: Input signal samples.
        b_coeffs: Numerator coefficients (b0, b1, b2).
        a_coeffs: Denominator coefficients (1.0, a1, a2).

    Returns:
        Filtered signal samples.
    """
    b0, b1, b2 = b_coeffs
    _, a1, a2 = a_coeffs

    x1 = x2 = 0.0
    y1 = y2 = 0.0
    output = []

    for x0 in samples:
        y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        output.append(y0)
        x2 = x1
        x1 = x0
        y2 = y1
        y1 = y0

    return output


def bandpass_filter(samples, freq_low, freq_high, sampling_rate):
    """Apply bandpass filter to signal samples.

    Convenience function that computes coefficients and applies the
    biquad filter in one step.

    Args:
        samples: Input signal samples.
        freq_low: Lower cutoff frequency in Hz.
        freq_high: Upper cutoff frequency in Hz.
        sampling_rate: Sampling rate in Hz.

    Returns:
        Bandpass filtered signal samples.
    """
    b_coeffs, a_coeffs = compute_biquad_coefficients(freq_low, freq_high, sampling_rate)
    return apply_biquad_filter(samples, b_coeffs, a_coeffs)


def compose_filter_cascade(stages):
    """Compose multiple biquad stages into a single transfer function.

    Convolves numerator and denominator polynomials from multiple
    stages to produce an equivalent higher-order filter representation.

    Args:
        stages: List of (b_coeffs, a_coeffs) tuples.

    Returns:
        Tuple of (combined_b, combined_a) polynomial coefficients.
    """
    if not stages:
        return ([1.0], [1.0])

    def convolve_poly(p1, p2):
        n = len(p1) + len(p2) - 1
        result = [0.0] * n
        for i, c1 in enumerate(p1):
            for j, c2 in enumerate(p2):
                result[i + j] += c1 * c2
        return result

    combined_b = list(stages[0][0])
    combined_a = list(stages[0][1])

    for i in range(1, len(stages)):
        combined_b = convolve_poly(combined_b, list(stages[i][0]))
        combined_a = convolve_poly(combined_a, list(stages[i][1]))

    return combined_b, combined_a


def compute_cascade_gain(combined_b, combined_a, frequency, sampling_rate):
    """Compute gain of cascaded filter at a specific frequency.

    Evaluates the transfer function H(z) at the given frequency point
    on the unit circle.

    Args:
        combined_b: Numerator polynomial coefficients.
        combined_a: Denominator polynomial coefficients.
        frequency: Evaluation frequency in Hz.
        sampling_rate: Sampling rate in Hz.

    Returns:
        Magnitude gain at the specified frequency.
    """
    omega = 2 * math.pi * frequency / sampling_rate

    num_real = 0.0
    num_imag = 0.0
    for k, coeff in enumerate(combined_b):
        num_real += coeff * math.cos(-k * omega)
        num_imag += coeff * math.sin(-k * omega)

    den_real = 0.0
    den_imag = 0.0
    for k, coeff in enumerate(combined_a):
        den_real += coeff * math.cos(-k * omega)
        den_imag += coeff * math.sin(-k * omega)

    num_mag = math.sqrt(num_real ** 2 + num_imag ** 2)
    den_mag = math.sqrt(den_real ** 2 + den_imag ** 2)

    if den_mag < 1e-10:
        return 0.0
    return num_mag / den_mag


def normalize_filter_gain(b_coeffs, a_coeffs, target_freq, sampling_rate):
    """Normalize filter gain to unity at the target frequency.

    Scales the numerator coefficients so the filter has 0 dB gain
    at the center of the passband.

    Args:
        b_coeffs: Original numerator coefficients.
        a_coeffs: Denominator coefficients.
        target_freq: Frequency where gain should be 1.0.
        sampling_rate: Sampling rate in Hz.

    Returns:
        Normalized numerator coefficients.
    """
    gain = compute_cascade_gain(list(b_coeffs), list(a_coeffs),
                                target_freq, sampling_rate)
    if gain < 1e-10:
        return b_coeffs

    scale = 1.0 / gain
    return tuple(b * scale for b in b_coeffs)
