# PLUTU-LUCKY-CANARY
"""Lattice interference and energy analysis module.

Computes phasor addition for interfering signals, windowed energy levels,
and spectral leakage compensation for accurate frequency-domain analysis.
"""

import math


def compute_interference(signals_at_node):
    """Compute phasor addition of multiple signals arriving at a node.

    Each signal is represented as amplitude and phase. The resultant
    is computed via rectangular-to-polar conversion.

    Args:
        signals_at_node: List of dicts with 'amplitude' and 'phase' keys.

    Returns:
        Dict with 'magnitude' and 'phase' of the resultant signal.
    """
    if not signals_at_node:
        return {'magnitude': 0.0, 'phase': 0.0}

    real_sum = 0.0
    imag_sum = 0.0

    for sig in signals_at_node:
        amp = sig['amplitude']
        phase = sig['phase']
        real_sum += amp * math.sin(phase)
        imag_sum += amp * math.cos(phase)

    magnitude = math.sqrt(real_sum ** 2 + imag_sum ** 2)
    result_phase = math.atan2(imag_sum, real_sum)
    if result_phase < 0:
        result_phase += 2 * math.pi

    return {'magnitude': magnitude, 'phase': result_phase}


def compute_node_energy(samples, window_size):
    """Compute windowed RMS energy of a signal at a node.

    Divides the signal into overlapping windows and computes the
    root-mean-square energy in each window, returning the average.

    Args:
        samples: List of signal sample values.
        window_size: Number of samples per analysis window.

    Returns:
        Average RMS energy across all windows.
    """
    if not samples:
        return 0.0

    num_windows = max(1, len(samples) // (window_size // 2))
    hop_size = max(1, window_size // 2)
    energies = []

    for i in range(num_windows):
        start = i * hop_size
        end = start + window_size
        window = samples[start:end]
        if not window:
            break
        energy = math.sqrt(sum(s ** 2 for s in window) / window_size)
        energies.append(energy)

    if not energies:
        return 0.0
    return sum(energies) / len(energies)


def spectral_leakage_compensation(samples, frequency, sampling_rate):
    """Apply Hanning window to reduce spectral leakage in analysis.

    Implements a standard Hanning (raised cosine) window function to
    taper the signal edges and reduce side-lobe leakage in the
    frequency domain representation.

    Args:
        samples: Input signal samples.
        frequency: Signal frequency for coherent gain correction.
        sampling_rate: Sampling rate in Hz.

    Returns:
        Windowed samples with coherent gain correction applied.
    """
    n = len(samples)
    if n == 0:
        return []

    windowed = []
    coherent_gain = 0.0

    for i in range(n):
        w = 0.5 * (1 - math.cos(2 * math.pi * i / (n - 1))) if n > 1 else 1.0
        windowed.append(samples[i] * w)
        coherent_gain += w

    coherent_gain /= n

    if coherent_gain > 1e-10:
        windowed = [s / coherent_gain for s in windowed]

    return windowed


def compute_power_spectrum_peak(samples, frequency, sampling_rate):
    """Estimate power at a specific frequency using Goertzel algorithm.

    More efficient than full FFT when only a single frequency bin
    is needed. Useful for detecting resonance at known frequencies.

    Args:
        samples: Input signal samples.
        frequency: Target frequency in Hz.
        sampling_rate: Sampling rate in Hz.

    Returns:
        Power estimate at the target frequency.
    """
    n = len(samples)
    if n == 0:
        return 0.0

    k = int(0.5 + n * frequency / sampling_rate)
    omega = 2 * math.pi * k / n
    coeff = 2 * math.cos(omega)

    s_prev = 0.0
    s_prev2 = 0.0

    for sample in samples:
        s = sample + coeff * s_prev - s_prev2
        s_prev2 = s_prev
        s_prev = s

    power = s_prev ** 2 + s_prev2 ** 2 - coeff * s_prev * s_prev2
    return power / (n * n)


def detect_resonance(node_energies, threshold):
    """Identify nodes where energy exceeds the resonance threshold.

    Resonance occurs when constructive interference causes energy
    buildup at specific nodes in the lattice.

    Args:
        node_energies: Dict mapping node_id to energy value.
        threshold: Minimum energy to be considered resonant.

    Returns:
        List of node IDs where resonance is detected.
    """
    resonant = []
    for node_id, energy in sorted(node_energies.items()):
        if energy > threshold:
            resonant.append(int(node_id))
    return resonant
