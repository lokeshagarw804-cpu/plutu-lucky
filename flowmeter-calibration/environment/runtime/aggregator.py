"""Interval aggregator — groups readings into fixed-duration buckets.

Collects compensated readings into time intervals and computes summary
statistics (mean flow) for each interval per meter.
"""
import configparser


class IntervalAggregator:
    """Groups readings into time intervals and computes interval averages."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._interval_sec = self._config.getint("aggregation", "interval_seconds")
        self._method = self._config.get("aggregation", "method")

    def aggregate(self, compensated_meters):
        """Aggregate readings into fixed-duration intervals.

        Each reading is assigned to an interval based on its timestamp.
        Interval boundaries use half-open ranges [start, end).

        Returns dict mapping meter_id to list of interval summary dicts with
        keys: interval_index, start_time, end_time, reading_count,
              mean_flow_raw, mean_flow_compensated, readings.
        """
        aggregated = {}
        for meter_id, readings in compensated_meters.items():
            intervals = {}
            for r in readings:
                ts = r["timestamp"]
                idx = self._assign_interval(ts)
                if idx not in intervals:
                    intervals[idx] = []
                intervals[idx].append(r)

            interval_list = []
            for idx in sorted(intervals.keys()):
                bucket = intervals[idx]
                count = len(bucket)

                if self._method == "mean":
                    mean_raw = sum(r["flow_raw"] for r in bucket) / count
                    mean_comp = sum(r["flow_compensated"] for r in bucket) / count
                else:
                    sorted_raw = sorted(r["flow_raw"] for r in bucket)
                    sorted_comp = sorted(r["flow_compensated"] for r in bucket)
                    mid = count // 2
                    mean_raw = sorted_raw[mid]
                    mean_comp = sorted_comp[mid]

                interval_list.append({
                    "interval_index": idx,
                    "start_time": idx * self._interval_sec,
                    "end_time": (idx + 1) * self._interval_sec,
                    "reading_count": count,
                    "mean_flow_raw": round(mean_raw, 4),
                    "mean_flow_compensated": round(mean_comp, 4),
                    "readings": bucket,
                })
            aggregated[meter_id] = interval_list
        return aggregated

    def _assign_interval(self, timestamp):
        """Assign a timestamp to its containing interval.

        Uses closed-start, open-end semantics: a reading at exactly
        the boundary between two intervals belongs to the ending interval
        (i.e., the interval whose end_time equals the timestamp).
        """
        idx = timestamp // self._interval_sec
        if timestamp > 0 and timestamp % self._interval_sec == 0:
            idx -= 1
        return idx
