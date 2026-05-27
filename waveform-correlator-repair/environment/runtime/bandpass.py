"""Bandpass filter — FIR approximation for seismic frequency isolation.

Implements a simple FIR bandpass filter using cascaded moving-average
operations. The filter removes frequencies below lowcut_hz and above
highcut_hz, isolating the seismic frequency band of interest.

This is a simplified implementation suitable for demonstration; real
seismic processing would use a proper Butterworth or zero-phase filter.
"""


def apply_fir_bandpass(signal, sample_rate, lowcut_hz, highcut_hz):
    """Apply FIR bandpass filter to isolate the target frequency band.

    Strategy: Apply low-pass (moving average at highcut period) then
    subtract the low-frequency baseline (moving average at lowcut period)
    to achieve bandpass effect.

    Args:
        signal: Input waveform samples (list of floats)
        sample_rate: Sampling rate in Hz
        lowcut_hz: Low corner frequency in Hz
        highcut_hz: High corner frequency in Hz

    Returns:
        Filtered waveform samples (list of floats)
    """
    n = len(signal)
    if n == 0:
        return signal

    # Low-pass stage: smooth with window corresponding to highcut frequency
    lp_half_width = max(1, int(round(sample_rate / highcut_hz)) // 2)
    low_passed = []
    for i in range(n):
        start = max(0, i - lp_half_width)
        end = min(n, i + lp_half_width + 1)
        window_sum = sum(signal[start:end])
        low_passed.append(window_sum / (end - start))

    # High-pass stage: subtract baseline at lowcut frequency
    hp_half_width = max(1, int(round(sample_rate / lowcut_hz)) // 2)
    band_passed = []
    for i in range(n):
        start = max(0, i - hp_half_width)
        end = min(n, i + hp_half_width + 1)
        baseline = sum(low_passed[start:end]) / (end - start)
        band_passed.append(low_passed[i] - baseline)

    return band_passed
