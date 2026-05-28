# PLUTU-LUCKY-CANARY
"""Timing calibration and quantization for lattice signal arrival times.

Handles timestamp quantization to simulation time steps, jitter
compensation, and temporal alignment of multi-path arrivals.
"""

import math


def quantize_arrival_time(arrival_time, time_step):
    """Quantize a continuous arrival time to the nearest simulation bin.

    Maps continuous-time signal arrivals to discrete simulation time
    slots for proper temporal alignment and interference computation.

    Args:
        arrival_time: Continuous arrival time in seconds.
        time_step: Simulation time step in seconds.

    Returns:
        Quantized bin index.
    """
    bin_index = int(arrival_time / time_step)
    return bin_index


def calibrate_arrivals(arrivals, time_step):
    """Calibrate and bin all signal arrivals at a node.

    Groups signals by their quantized arrival bin for interference
    computation. Signals in the same bin interfere constructively
    or destructively.

    Args:
        arrivals: List of dicts with 'delay', 'amplitude', 'phase', 'frequency'.
        time_step: Simulation time step in seconds.

    Returns:
        Dict mapping bin_index to list of signals arriving in that bin.
    """
    bins = {}
    for arrival in arrivals:
        bin_idx = quantize_arrival_time(arrival['delay'], time_step)
        if bin_idx not in bins:
            bins[bin_idx] = []
        bins[bin_idx].append(arrival)
    return bins


def compute_jitter_statistics(arrivals, time_step):
    """Compute jitter statistics for signal arrivals at a node.

    Tracks the deviation between actual arrival times and their
    quantized bin centers. Used for quality assessment of the
    temporal calibration.

    Args:
        arrivals: List of dicts with 'delay' key.
        time_step: Simulation time step in seconds.

    Returns:
        Dict with 'mean_jitter', 'max_jitter', 'std_jitter'.
    """
    if not arrivals:
        return {'mean_jitter': 0.0, 'max_jitter': 0.0, 'std_jitter': 0.0}

    jitters = []
    for arrival in arrivals:
        bin_idx = quantize_arrival_time(arrival['delay'], time_step)
        bin_center = (bin_idx + 0.5) * time_step
        jitter = abs(arrival['delay'] - bin_center)
        jitters.append(jitter)

    mean_jitter = sum(jitters) / len(jitters)
    max_jitter = max(jitters)

    variance = sum((j - mean_jitter) ** 2 for j in jitters) / len(jitters)
    std_jitter = math.sqrt(variance)

    return {
        'mean_jitter': mean_jitter,
        'max_jitter': max_jitter,
        'std_jitter': std_jitter
    }


def compensate_jitter(arrivals, time_step, compensation_factor=0.5):
    """Apply jitter compensation to signal arrivals.

    Adjusts signal phases to account for the temporal offset between
    actual arrival and the quantized bin center. Uses linear phase
    correction proportional to the time offset.

    Args:
        arrivals: List of dicts with 'delay', 'phase', 'frequency' keys.
        time_step: Simulation time step in seconds.
        compensation_factor: Fraction of jitter to compensate (0 to 1).

    Returns:
        List of arrivals with compensated phase values.
    """
    compensated = []
    for arrival in arrivals:
        bin_idx = quantize_arrival_time(arrival['delay'], time_step)
        bin_center = (bin_idx + 0.5) * time_step
        time_offset = arrival['delay'] - bin_center

        phase_correction = 2 * math.pi * arrival['frequency'] * time_offset
        adjusted_phase = arrival['phase'] + compensation_factor * phase_correction
        adjusted_phase = adjusted_phase % (2 * math.pi)

        compensated_arrival = dict(arrival)
        compensated_arrival['phase'] = adjusted_phase
        compensated.append(compensated_arrival)

    return compensated


def compute_temporal_coherence(bin_signals):
    """Assess temporal coherence of signals within a time bin.

    Measures how well-aligned signals are within their quantization
    bin. High coherence indicates the signals truly arrive simultaneously.

    Args:
        bin_signals: List of signal dicts within one time bin.

    Returns:
        Coherence metric between 0 and 1.
    """
    if len(bin_signals) <= 1:
        return 1.0

    phases = [s['phase'] for s in bin_signals]
    mean_phase = sum(phases) / len(phases)

    phase_variance = sum((p - mean_phase) ** 2 for p in phases) / len(phases)
    coherence = math.exp(-phase_variance)

    return coherence
