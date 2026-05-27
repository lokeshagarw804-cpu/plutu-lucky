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

        Each reading is assigned to interval: floor(timestamp / interval_seconds).
        Interval boundaries are [start, start + interval_seconds).

        Returns dict mapping meter_id to list of interval summary dicts with
        keys: interval_index, start_time, end_time, reading_count,
              mean_flow_raw, mean_flow_compensated, readings.
        """
        aggregated = {}
        for meter_id, readings in compensated_meters.items():
            intervals = {}
            for r in readings:
                ts = r["timestamp"]
                # BUG: uses strict less-than for upper boundary
                # interval_index should be: ts // interval_seconds
                # but this manual boundary check excludes readings at exact boundaries
                # e.g., timestamp=60 should be in interval 1, but this puts it nowhere
                # when a reading falls exactly on a boundary
                idx = self._find_interval(ts)
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

    def _find_interval(self, timestamp):
        """Determine which interval a timestamp belongs to.

        Interval boundaries: [n*interval, (n+1)*interval)
        A reading at exactly (n+1)*interval starts the next interval.
        """
        # BUG: for timestamps that are exact multiples of interval_seconds,
        # this incorrectly subtracts 1, putting boundary readings in the prior interval
        # e.g., timestamp=60 with interval=60 gives idx=0 instead of idx=1
        idx = timestamp // self._interval_sec
        if timestamp > 0 and timestamp % self._interval_sec == 0:
            idx -= 1
        return idx
