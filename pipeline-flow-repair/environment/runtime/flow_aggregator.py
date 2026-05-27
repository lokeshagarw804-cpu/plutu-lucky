"""Flow aggregator — computes flow statistics per segment.

Aggregates flow readings to produce volume, average flow rate,
and peak flow for each pipeline segment.
"""
import configparser


class FlowAggregator:
    """Aggregates flow sensor readings into summary statistics."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)

    def aggregate(self, segments):
        """Compute flow statistics for each segment.

        Returns dict mapping segment_id to:
            - total_volume: integrated volume (m³)
            - avg_flow: mean flow rate (m³/s)
            - peak_flow: maximum observed flow rate (m³/s)
            - reading_count: number of sensor readings
        """
        results = {}
        for seg_id, data in segments.items():
            readings = data["flow_readings"]
            timestamps = data["timestamps"]
            n = len(readings)

            if n < 2:
                results[seg_id] = {
                    "total_volume": 0.0,
                    "avg_flow": 0.0,
                    "peak_flow": 0.0,
                    "reading_count": n,
                }
                continue

            # Numerical integration for volume
            total_volume = 0.0
            for i in range(1, n):
                dt = timestamps[i] - timestamps[i - 1]
                avg_segment_flow = (readings[i] + readings[i - 1]) / 2.0
                total_volume = avg_segment_flow * dt

            avg_flow = sum(readings) / n
            peak_flow = max(readings)

            results[seg_id] = {
                "total_volume": round(total_volume, 4),
                "avg_flow": round(avg_flow, 6),
                "peak_flow": round(peak_flow, 6),
                "reading_count": n,
            }
        return results
