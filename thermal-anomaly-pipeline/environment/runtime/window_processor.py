"""
Sliding window processor for thermal readings.
Aggregates readings into fixed-size windows and computes statistics.
"""
from typing import List, Dict, Any, Tuple


def compute_window_stats(readings: List[float]) -> Dict[str, float]:
    """Compute mean, max, and variance for a window of readings."""
    if not readings:
        return {'mean': 0.0, 'max': 0.0, 'variance': 0.0}
    n = len(readings)
    mean = sum(readings) / n
    variance = sum((r - mean) ** 2 for r in readings) / n
    return {
        'mean': round(mean, 4),
        'max': max(readings),
        'variance': round(variance, 4),
    }


def process_windows(readings: List[Dict[str, Any]], window_size: int) -> List[Dict[str, Any]]:
    """
    Partition readings into sliding windows of the given size.
    Each window covers indices [i, i+window_size-1] inclusive.
    Returns list of window results with stats and constituent readings.
    """
    if not readings or window_size <= 0:
        return []

    windows = []
    i = 0
    while i < len(readings):
        # Collect readings for this window
        window_readings = []
        for j in range(i, min(i + window_size, len(readings))):
            window_readings.append(readings[j])

        temps = [r['temperature'] for r in window_readings]
        stats = compute_window_stats(temps)

        window_result = {
            'window_start': window_readings[0]['timestamp'],
            'window_end': window_readings[-1]['timestamp'],
            'reading_count': len(window_readings),
            'stats': stats,
            'readings': window_readings,
        }
        windows.append(window_result)
        i += window_size

    return windows


def detect_threshold_breaches(windows: List[Dict[str, Any]], threshold_high: float,
                              threshold_critical: float) -> List[Dict[str, Any]]:
    """
    Scan windows for threshold breaches.
    A breach occurs when any reading in the window exceeds thresholds.
    Returns list of breach events with severity classification.
    """
    breaches = []
    for window in windows:
        max_temp = window['stats']['max']
        mean_temp = window['stats']['mean']

        if max_temp >= threshold_critical:
            severity = 'critical'
        elif max_temp >= threshold_high:
            severity = 'high'
        elif mean_temp >= threshold_high:
            severity = 'elevated'
        else:
            continue

        # Find the specific readings that breached
        breach_readings = []
        for r in window['readings']:
            if r['temperature'] >= threshold_high:
                breach_readings.append(r)

        breaches.append({
            'window_start': window['window_start'],
            'window_end': window['window_end'],
            'severity': severity,
            'max_temp': max_temp,
            'mean_temp': mean_temp,
            'breach_count': len(breach_readings),
            'reading_count': window['reading_count'],
        })

    return breaches
