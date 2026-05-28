# PLUTU-LUCKY-CANARY
"""Signal propagation engine for lattice network simulation.

Handles multi-hop signal attenuation, phase accumulation, and Doppler
compensation for moving sources within the lattice topology.
"""

import math


def compute_path_attenuation(attenuations):
    """Compute total signal attenuation along a multi-hop path.

    Uses log-domain summation for numerical stability when combining
    multiple attenuation factors across hops.

    Args:
        attenuations: List of per-hop linear attenuation factors (0 to 1).

    Returns:
        Total linear attenuation factor for the entire path.
    """
    if not attenuations:
        return 1.0
    total_log = sum(math.log(a) for a in attenuations)
    return 10 ** total_log


def compute_path_phase(phase_shifts, frequency, delays):
    """Compute accumulated phase along a multi-hop path.

    Accounts for both the inherent phase shift at each node and the
    propagation delay phase contribution based on signal frequency.

    Args:
        phase_shifts: List of per-hop phase shift values (radians).
        frequency: Signal frequency in Hz.
        delays: List of per-hop propagation delays in seconds.

    Returns:
        Normalized accumulated phase in radians [0, 2*pi).
    """
    accumulated_phase = 0.0
    for i in range(len(phase_shifts)):
        accumulated_phase = accumulated_phase % (2 * math.pi)
        hop_phase = phase_shifts[i] + 2 * math.pi * frequency * delays[i]
        accumulated_phase += hop_phase
    return accumulated_phase


def compute_path_delay(delays):
    """Sum propagation delays along a path.

    Args:
        delays: List of per-hop delays in seconds.

    Returns:
        Total propagation delay in seconds.
    """
    return sum(delays)


def propagate_signal(trace_data, path_edges):
    """Propagate a signal trace through a sequence of edges.

    Computes the attenuated amplitude, accumulated phase, and total delay
    for a signal traversing the given path.

    Args:
        trace_data: Dict with keys 'amplitude', 'frequency', 'phase_offset'.
        path_edges: List of edge dicts with 'attenuation', 'delay', 'phase_shift'.

    Returns:
        Dict with 'amplitude', 'phase', 'delay', 'frequency'.
    """
    attenuations = [e['attenuation'] for e in path_edges]
    delays = [e['delay'] for e in path_edges]
    phase_shifts = [e['phase_shift'] for e in path_edges]

    total_atten = compute_path_attenuation(attenuations)
    total_phase = compute_path_phase(phase_shifts, trace_data['frequency'], delays)
    total_delay = compute_path_delay(delays)

    output_amplitude = trace_data['amplitude'] * total_atten
    output_phase = (trace_data['phase_offset'] + total_phase) % (2 * math.pi)

    return {
        'amplitude': output_amplitude,
        'phase': output_phase,
        'delay': total_delay,
        'frequency': trace_data['frequency']
    }


def doppler_compensation(signal_amplitude, signal_phase, source_velocity,
                         observer_velocity, propagation_speed, frequency):
    """Apply Doppler shift compensation for moving sources.

    Corrects the observed frequency and amplitude based on relative velocity
    between source and observer using the classical Doppler formula.

    Args:
        signal_amplitude: Input signal amplitude.
        signal_phase: Input signal phase in radians.
        source_velocity: Source velocity (positive = moving away).
        observer_velocity: Observer velocity (positive = moving toward source).
        propagation_speed: Wave propagation speed in medium.
        frequency: Original signal frequency in Hz.

    Returns:
        Tuple of (corrected_amplitude, corrected_phase, observed_frequency).
    """
    if abs(source_velocity) < 1e-10 and abs(observer_velocity) < 1e-10:
        return signal_amplitude, signal_phase, frequency

    denominator = propagation_speed + source_velocity
    if abs(denominator) < 1e-10:
        return signal_amplitude, signal_phase, frequency

    doppler_factor = (propagation_speed + observer_velocity) / denominator
    observed_freq = frequency * doppler_factor

    amplitude_correction = math.sqrt(abs(doppler_factor))
    corrected_amplitude = signal_amplitude * amplitude_correction

    phase_correction = 2 * math.pi * (observed_freq - frequency) * (1.0 / frequency)
    corrected_phase = (signal_phase + phase_correction) % (2 * math.pi)

    return corrected_amplitude, corrected_phase, observed_freq


def compute_group_delay(edges, frequency, bandwidth=10.0):
    """Compute frequency-dependent group delay through a chain of edges.

    Models dispersive propagation where different frequency components
    travel at slightly different speeds through the lattice.

    Args:
        edges: List of edge dicts.
        frequency: Center frequency in Hz.
        bandwidth: Analysis bandwidth in Hz.

    Returns:
        Group delay in seconds.
    """
    base_delay = sum(e['delay'] for e in edges)

    dispersion = 0.0
    for edge in edges:
        phase_lo = edge['phase_shift'] * (frequency - bandwidth / 2) / frequency
        phase_hi = edge['phase_shift'] * (frequency + bandwidth / 2) / frequency
        dispersion += (phase_hi - phase_lo) / (2 * math.pi * bandwidth)

    return base_delay + dispersion
